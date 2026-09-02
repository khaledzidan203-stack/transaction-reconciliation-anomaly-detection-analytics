"""Explainable matching engine: deterministic hierarchical matcher.

Implements the 8-level match method hierarchy defined in config.py.
Every match result includes the method used and a confidence score so
that downstream reconciliation and review logic is fully explainable.
"""

from __future__ import annotations

from typing import Any

import pandas as pd
from rapidfuzz import fuzz

from .config import (
    CONFIDENCE_BARCODE,
    CONFIDENCE_GENERIC_STRENGTH,
    CONFIDENCE_NORMALIZED_NAME,
    CONFIDENCE_POSSIBLE_SUBSTITUTE,
    CONFIDENCE_PRIMARY_ID,
    CONFIDENCE_PRODUCT_CODE,
    CONFIDENCE_UNMATCHED,
    FUZZY_ACCEPT_THRESHOLD,
    FUZZY_REVIEW_THRESHOLD,
    MATCH_EXACT_BARCODE,
    MATCH_EXACT_PRIMARY_ID,
    MATCH_EXACT_PRODUCT_CODE,
    MATCH_FUZZY_NAME,
    MATCH_GENERIC_STRENGTH,
    MATCH_NONE,
    MATCH_NORMALIZED_NAME,
    MATCH_POSSIBLE_SUBSTITUTE,
    SOURCE_A,
    SOURCE_B,
)
from .normalization import normalize_identifier, normalize_product_name


def _best_fuzzy_score(name_a: str, name_b: str) -> float:
    """Return the best fuzzy ratio between two normalized names."""
    if not name_a or not name_b:
        return 0.0
    sort_score = fuzz.token_sort_ratio(name_a, name_b) / 100.0
    partial_score = fuzz.partial_ratio(name_a, name_b) / 100.0
    return max(sort_score, partial_score)


def match_lines(
    a_lines: pd.DataFrame,
    b_lines: pd.DataFrame,
) -> pd.DataFrame:
    """Match Source A lines to Source B lines using the hierarchy.

    Returns a DataFrame with one row per Source A line, containing
    the best match found (or UNMATCHED) along with the method,
    confidence score and fuzzy details.
    """
    # Build B-line lookup indices for fast candidate retrieval
    b_by_txn_id: dict[str, list[int]] = {}
    b_by_barcode: dict[str, list[int]] = {}
    b_by_code: dict[str, list[int]] = {}
    b_by_norm_name: dict[str, list[int]] = {}
    b_by_generic: dict[str, list[int]] = {}

    for idx, row in b_lines.iterrows():
        txn = row.get("_norm_txn_id", "")
        if txn:
            b_by_txn_id.setdefault(txn, []).append(idx)
        bc = row.get("_norm_barcode", "")
        if bc:
            b_by_barcode.setdefault(bc, []).append(idx)
        code = row.get("_norm_product_code", "")
        if code:
            b_by_code.setdefault(code, []).append(idx)
        nname = row.get("_norm_product_name", "")
        if nname:
            b_by_norm_name.setdefault(nname, []).append(idx)
        generic = normalize_product_name(row.get("generic_name", ""))
        if generic:
            b_by_generic.setdefault(generic, []).append(idx)

    results: list[dict[str, Any]] = []
    consumed_b_indices: set[int] = set()

    for a_idx, a_row in a_lines.iterrows():
        a_txn_id = a_row.get("_norm_txn_id", "")
        a_ref_id = a_row.get("_norm_reference_id", "")
        a_product_id = normalize_identifier(a_row.get("product_id", ""))
        a_barcode = a_row.get("_norm_barcode", "")
        a_code = a_row.get("_norm_product_code", "")
        a_norm_name = a_row.get("_norm_product_name", "")
        a_generic = normalize_product_name(a_row.get("generic_name", ""))
        a_line_id = a_row.get("line_id", "")

        matched_method = MATCH_NONE
        matched_confidence = CONFIDENCE_UNMATCHED
        matched_b_idx: int | None = None
        fuzzy_score: float = 0.0
        fuzzy_threshold_band: str = ""

        # Level 1: EXACT_PRIMARY_ID — A reference_id == B transaction_id AND product_id matches
        if a_ref_id and matched_method == MATCH_NONE:
            candidates = b_by_txn_id.get(a_ref_id, [])
            for b_idx in candidates:
                if b_idx in consumed_b_indices:
                    continue
                b_row = b_lines.loc[b_idx]
                if normalize_identifier(b_row.get("product_id", "")) == a_product_id:
                    matched_method = MATCH_EXACT_PRIMARY_ID
                    matched_confidence = CONFIDENCE_PRIMARY_ID
                    matched_b_idx = b_idx
                    break

        # Level 2: EXACT_BARCODE
        if matched_method == MATCH_NONE and a_barcode:
            candidates = b_by_barcode.get(a_barcode, [])
            for b_idx in candidates:
                if b_idx in consumed_b_indices:
                    continue
                matched_method = MATCH_EXACT_BARCODE
                matched_confidence = CONFIDENCE_BARCODE
                matched_b_idx = b_idx
                break

        # Level 3: EXACT_PRODUCT_CODE
        if matched_method == MATCH_NONE and a_code:
            candidates = b_by_code.get(a_code, [])
            for b_idx in candidates:
                if b_idx in consumed_b_indices:
                    continue
                matched_method = MATCH_EXACT_PRODUCT_CODE
                matched_confidence = CONFIDENCE_PRODUCT_CODE
                matched_b_idx = b_idx
                break

        # Level 4: NORMALIZED_NAME
        if matched_method == MATCH_NONE and a_norm_name:
            candidates = b_by_norm_name.get(a_norm_name, [])
            for b_idx in candidates:
                if b_idx in consumed_b_indices:
                    continue
                matched_method = MATCH_NORMALIZED_NAME
                matched_confidence = CONFIDENCE_NORMALIZED_NAME
                matched_b_idx = b_idx
                break

        # Level 5: FUZZY_NAME — scan B lines with shared generic name first
        if matched_method == MATCH_NONE and a_norm_name:
            # Gather candidate B indices from generic name pool
            candidate_pool: set[int] = set()
            if a_generic:
                for b_idx in b_by_generic.get(a_generic, []):
                    if b_idx not in consumed_b_indices:
                        candidate_pool.add(b_idx)
            # If generic pool is empty, fall back to all unconsumed B lines
            if not candidate_pool:
                candidate_pool = {i for i in b_lines.index if i not in consumed_b_indices}

            best_score = 0.0
            best_b_idx = None
            for b_idx in candidate_pool:
                b_row = b_lines.loc[b_idx]
                b_norm_name = b_row.get("_norm_product_name", "")
                if not b_norm_name:
                    continue
                score = _best_fuzzy_score(a_norm_name, b_norm_name)
                if score > best_score:
                    best_score = score
                    best_b_idx = b_idx
            if best_score >= FUZZY_ACCEPT_THRESHOLD:
                matched_method = MATCH_FUZZY_NAME
                matched_confidence = round(best_score * 100, 1)
                matched_b_idx = best_b_idx
                fuzzy_score = best_score
                fuzzy_threshold_band = "ACCEPT"
            elif best_score >= FUZZY_REVIEW_THRESHOLD:
                matched_method = MATCH_FUZZY_NAME
                matched_confidence = round(best_score * 100, 1)
                matched_b_idx = best_b_idx
                fuzzy_score = best_score
                fuzzy_threshold_band = "REVIEW"

        # Level 6: GENERIC_STRENGTH_EQUIVALENT — same generic + strength, different brand
        if matched_method == MATCH_NONE and a_generic:
            candidates = b_by_generic.get(a_generic, [])
            for b_idx in candidates:
                if b_idx in consumed_b_indices:
                    continue
                b_row = b_lines.loc[b_idx]
                b_norm_name = b_row.get("_norm_product_name", "")
                # Brand must differ (otherwise Level 4 would have matched)
                if b_norm_name != a_norm_name:
                    matched_method = MATCH_GENERIC_STRENGTH
                    matched_confidence = CONFIDENCE_GENERIC_STRENGTH
                    matched_b_idx = b_idx
                    break

        # Level 7: POSSIBLE_SUBSTITUTE — fuzzy generic match
        if matched_method == MATCH_NONE and a_generic:
            best_score = 0.0
            best_b_idx = None
            for b_idx, b_row in b_lines.iterrows():
                if b_idx in consumed_b_indices:
                    continue
                b_generic = normalize_product_name(b_row.get("generic_name", ""))
                if not b_generic:
                    continue
                score = _best_fuzzy_score(a_generic, b_generic)
                if score >= 0.70 and score > best_score:
                    best_score = score
                    best_b_idx = b_idx
            if best_b_idx is not None:
                matched_method = MATCH_POSSIBLE_SUBSTITUTE
                matched_confidence = CONFIDENCE_POSSIBLE_SUBSTITUTE
                matched_b_idx = best_b_idx
                fuzzy_score = best_score

        # Mark B line as consumed
        if matched_b_idx is not None:
            consumed_b_indices.add(matched_b_idx)

        # Collect result
        b_line_id = ""
        b_txn_id = ""
        b_product_id = ""
        if matched_b_idx is not None:
            b_row = b_lines.loc[matched_b_idx]
            b_line_id = b_row.get("line_id", "")
            b_txn_id = b_row.get("transaction_id", "")
            b_product_id = b_row.get("product_id", "")

        results.append({
            "source_a_line_id": a_line_id,
            "source_a_transaction_id": a_row.get("transaction_id", ""),
            "source_a_product_id": a_row.get("product_id", ""),
            "source_b_line_id": b_line_id,
            "source_b_transaction_id": b_txn_id,
            "source_b_product_id": b_product_id,
            "match_method": matched_method,
            "confidence_score": matched_confidence,
            "fuzzy_score": round(fuzzy_score, 4),
            "fuzzy_threshold_band": fuzzy_threshold_band,
        })

    return pd.DataFrame(results)
