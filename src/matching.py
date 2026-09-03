"""Explainable matching engine: deterministic hierarchical matcher.

Implements the 8-level match method hierarchy defined in config.py.
Every match result includes the method used and a confidence score so
that downstream reconciliation and review logic is fully explainable.

Performance: uses inverted token indices to avoid O(n²) full scans
in the fuzzy matching levels.
"""

from __future__ import annotations

from collections import defaultdict
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
    REVIEW_CONFIDENCE_FLOOR,
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


def _build_token_index(frame: pd.DataFrame, col: str) -> dict[str, set[int]]:
    """Build a token → set of row indices inverted index."""
    index: dict[str, set[int]] = defaultdict(set)
    for idx, row in frame.iterrows():
        val = row.get(col, "")
        if val:
            for token in str(val).split():
                if len(token) >= 3:
                    index[token].add(idx)
    return dict(index)


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
    b_by_txn_id: dict[str, list[int]] = defaultdict(list)
    b_by_barcode: dict[str, list[int]] = defaultdict(list)
    b_by_code: dict[str, list[int]] = defaultdict(list)
    b_by_norm_name: dict[str, list[int]] = defaultdict(list)
    b_by_generic: dict[str, list[int]] = defaultdict(list)

    for idx, row in b_lines.iterrows():
        txn = row.get("_norm_txn_id", "")
        if txn:
            b_by_txn_id[txn].append(idx)
        bc = row.get("_norm_barcode", "")
        if bc:
            b_by_barcode[bc].append(idx)
        code = row.get("_norm_product_code", "")
        if code:
            b_by_code[code].append(idx)
        nname = row.get("_norm_product_name", "")
        if nname:
            b_by_norm_name[nname].append(idx)
        generic = normalize_product_name(row.get("generic_name", ""))
        if generic:
            b_by_generic[generic].append(idx)

    # Build token-based inverted index for B norm_product_name (fuzzy candidates)
    b_name_token_index = _build_token_index(b_lines, "_norm_product_name")

    results: list[dict[str, Any]] = []
    consumed_b_indices: set[int] = set()

    for a_idx, a_row in a_lines.iterrows():
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
        if a_ref_id:
            for b_idx in b_by_txn_id.get(a_ref_id, []):
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
            for b_idx in b_by_barcode.get(a_barcode, []):
                if b_idx not in consumed_b_indices:
                    matched_method = MATCH_EXACT_BARCODE
                    matched_confidence = CONFIDENCE_BARCODE
                    matched_b_idx = b_idx
                    break

        # Level 3: EXACT_PRODUCT_CODE
        if matched_method == MATCH_NONE and a_code:
            for b_idx in b_by_code.get(a_code, []):
                if b_idx not in consumed_b_indices:
                    matched_method = MATCH_EXACT_PRODUCT_CODE
                    matched_confidence = CONFIDENCE_PRODUCT_CODE
                    matched_b_idx = b_idx
                    break

        # Level 4: NORMALIZED_NAME
        if matched_method == MATCH_NONE and a_norm_name:
            for b_idx in b_by_norm_name.get(a_norm_name, []):
                if b_idx not in consumed_b_indices:
                    matched_method = MATCH_NORMALIZED_NAME
                    matched_confidence = CONFIDENCE_NORMALIZED_NAME
                    matched_b_idx = b_idx
                    break

        # Level 5: FUZZY_NAME — use token index to find candidates
        if matched_method == MATCH_NONE and a_norm_name:
            candidate_pool: set[int] = set()
            for token in a_norm_name.split():
                if len(token) >= 3 and token in b_name_token_index:
                    candidate_pool.update(b_name_token_index[token])
            # Remove already consumed
            candidate_pool -= consumed_b_indices

            best_score = 0.0
            best_b_idx = None
            for b_idx in candidate_pool:
                b_norm_name = b_lines.at[b_idx, "_norm_product_name"] if b_idx in b_lines.index else ""
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
            for b_idx in b_by_generic.get(a_generic, []):
                if b_idx in consumed_b_indices:
                    continue
                b_norm_name = b_lines.at[b_idx, "_norm_product_name"] if b_idx in b_lines.index else ""
                if b_norm_name != a_norm_name:
                    matched_method = MATCH_GENERIC_STRENGTH
                    matched_confidence = CONFIDENCE_GENERIC_STRENGTH
                    matched_b_idx = b_idx
                    break

        # Level 7: POSSIBLE_SUBSTITUTE — fuzzy generic from generic index
        if matched_method == MATCH_NONE and a_generic:
            a_generic_first = a_generic.split()[0] if a_generic else ""
            candidate_b: set[int] = set()
            if a_generic_first:
                for pool_key, indices in b_by_generic.items():
                    if a_generic_first in pool_key.split():
                        candidate_b.update(indices)
            candidate_b -= consumed_b_indices

            best_score = 0.0
            best_b_idx = None
            for b_idx in candidate_b:
                b_generic = b_lines.at[b_idx, "generic_name"] if b_idx in b_lines.index else ""
                b_generic_norm = normalize_product_name(b_generic)
                if not b_generic_norm:
                    continue
                score = _best_fuzzy_score(a_generic, b_generic_norm)
                if score >= 0.70 and score > best_score:
                    best_score = score
                    best_b_idx = b_idx
            if best_b_idx is not None:
                matched_method = MATCH_POSSIBLE_SUBSTITUTE
                matched_confidence = CONFIDENCE_POSSIBLE_SUBSTITUTE
                matched_b_idx = best_b_idx
                fuzzy_score = best_score

        # Only consume B lines for deterministic matches or high-confidence
        # fuzzy matches.  Heuristic matches (GENERIC_STRENGTH, SUBSTITUTE)
        # and fuzzy matches below the confidence floor are reported as
        # potential matches but leave the B line free so reconciliation
        # can flag unconsumed B lines as MISSING_IN_SOURCE_A.
        _deterministic_methods = {
            MATCH_EXACT_PRIMARY_ID, MATCH_EXACT_BARCODE,
            MATCH_EXACT_PRODUCT_CODE, MATCH_NORMALIZED_NAME,
        }
        b_consumed = False
        if matched_b_idx is not None:
            if matched_method in _deterministic_methods:
                consumed_b_indices.add(matched_b_idx)
                b_consumed = True
            elif matched_confidence >= REVIEW_CONFIDENCE_FLOOR and matched_method == MATCH_FUZZY_NAME:
                consumed_b_indices.add(matched_b_idx)
                b_consumed = True
            # GENERIC_STRENGTH and POSSIBLE_SUBSTITUTE: report but don't consume

        # Collect result — if the B line was not consumed, treat as unmatched
        # for reconciliation purposes but keep the match_method and confidence
        # as metadata for the review queue.
        b_line_id = ""
        b_txn_id = ""
        b_product_id = ""
        if matched_b_idx is not None and b_consumed and matched_b_idx in b_lines.index:
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
