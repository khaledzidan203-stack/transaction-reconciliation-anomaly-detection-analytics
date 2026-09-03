"""Reconciliation engine: compare matched pairs and assign statuses.

For each matched line pair, identity/quantity/price/amount statuses are
computed independently. The overall reconciliation status is derived
from the combination of component statuses.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from .config import (
    AMOUNT_MATCHED,
    AMOUNT_NOT_APPLICABLE,
    AMOUNT_TOLERANCE,
    AMOUNT_VARIANCE,
    IDENTITY_MATCHED,
    IDENTITY_MISSING_A,
    IDENTITY_MISSING_B,
    IDENTITY_SUBSTITUTE,
    IDENTITY_UNMATCHED,
    MATCH_EXACT_BARCODE,
    MATCH_EXACT_PRIMARY_ID,
    MATCH_EXACT_PRODUCT_CODE,
    MATCH_FUZZY_NAME,
    MATCH_GENERIC_STRENGTH,
    MATCH_NONE,
    MATCH_NORMALIZED_NAME,
    MATCH_POSSIBLE_SUBSTITUTE,
    PRICE_MATCHED,
    PRICE_NOT_APPLICABLE,
    PRICE_VARIANCE,
    QUANTITY_EXCESS,
    QUANTITY_MATCHED,
    QUANTITY_NOT_APPLICABLE,
    QUANTITY_SHORTAGE,
    QUANTITY_TOLERANCE,
    REVIEW_CONFIDENCE_FLOOR,
    SOURCE_A,
    SOURCE_B,
    UNIT_PRICE_TOLERANCE,
    STATUS_ADDITIONAL_ITEM,
    STATUS_ADDITIONAL_TRANSACTION,
    STATUS_AMOUNT_DIFFERENCE,
    STATUS_CREDIT,
    STATUS_DATA_QUALITY_EXCEPTION,
    STATUS_DUPLICATE_KEY,
    STATUS_FUZZY_MATCH_REVIEW,
    STATUS_MATCHED,
    STATUS_MATCHED_WITH_SUBSTITUTE,
    STATUS_MASTER_DATA_EXCEPTION,
    STATUS_MISSING_IN_SOURCE_A,
    STATUS_MISSING_IN_SOURCE_B,
    STATUS_PRICE_DIFFERENCE,
    STATUS_QUANTITY_AND_AMOUNT_DIFFERENCE,
    STATUS_QUANTITY_DIFFERENCE,
    STATUS_REVERSAL,
    STATUS_UNRESOLVED,
    TXN_CREDIT,
    TXN_REVERSAL,
)
from .normalization import normalize_identifier


def _identity_status(match_method: str) -> str:
    """Map match method to identity component status."""
    if match_method in (MATCH_EXACT_PRIMARY_ID, MATCH_EXACT_BARCODE,
                        MATCH_EXACT_PRODUCT_CODE, MATCH_NORMALIZED_NAME):
        return IDENTITY_MATCHED
    if match_method in (MATCH_GENERIC_STRENGTH, MATCH_POSSIBLE_SUBSTITUTE):
        return IDENTITY_SUBSTITUTE
    if match_method == MATCH_FUZZY_NAME:
        return IDENTITY_SUBSTITUTE
    return IDENTITY_UNMATCHED


def _quantity_status(qty_a: float | None, qty_b: float | None) -> str:
    """Compare quantities and return the component status."""
    if qty_a is None or qty_b is None:
        return QUANTITY_NOT_APPLICABLE
    diff = abs(qty_a - qty_b)
    if diff <= QUANTITY_TOLERANCE:
        return QUANTITY_MATCHED
    if qty_a < qty_b:
        return QUANTITY_SHORTAGE
    return QUANTITY_EXCESS


def _price_status(price_a: float | None, price_b: float | None) -> str:
    """Compare unit prices and return the component status."""
    if price_a is None or price_b is None:
        return PRICE_NOT_APPLICABLE
    diff = abs(price_a - price_b)
    if diff <= UNIT_PRICE_TOLERANCE:
        return PRICE_MATCHED
    return PRICE_VARIANCE


def _amount_status(amt_a: float | None, amt_b: float | None) -> str:
    """Compare amounts and return the component status."""
    if amt_a is None or amt_b is None:
        return AMOUNT_NOT_APPLICABLE
    diff = abs(amt_a - amt_b)
    if diff <= AMOUNT_TOLERANCE:
        return AMOUNT_MATCHED
    return AMOUNT_VARIANCE


def _derive_reconciliation_status(
    identity: str, quantity: str, price: str, amount: str,
    match_method: str, confidence: float, txn_type: str,
    is_unmatched_a: bool, is_unmatched_b: bool,
) -> str:
    """Derive the overall reconciliation status from component statuses."""
    # Special transaction types
    if txn_type == TXN_CREDIT:
        return STATUS_CREDIT
    if txn_type == TXN_REVERSAL:
        return STATUS_REVERSAL

    # Unmatched sides
    if is_unmatched_a:
        return STATUS_MISSING_IN_SOURCE_A
    if is_unmatched_b:
        if identity == IDENTITY_UNMATCHED:
            return STATUS_UNRESOLVED
        return STATUS_MISSING_IN_SOURCE_B

    # Fuzzy review band
    if match_method == MATCH_FUZZY_NAME and confidence < REVIEW_CONFIDENCE_FLOOR:
        return STATUS_FUZZY_MATCH_REVIEW

    # Identity-level status
    if identity == IDENTITY_UNMATCHED:
        return STATUS_UNRESOLVED
    if identity == IDENTITY_SUBSTITUTE:
        base = STATUS_MATCHED_WITH_SUBSTITUTE
    else:
        base = STATUS_MATCHED

    # Quantity/price/amount variances override the base
    qty_issue = quantity in (QUANTITY_SHORTAGE, QUANTITY_EXCESS)
    price_issue = price == PRICE_VARIANCE
    amt_issue = amount == AMOUNT_VARIANCE

    if qty_issue and amt_issue:
        return STATUS_QUANTITY_AND_AMOUNT_DIFFERENCE
    if qty_issue:
        return STATUS_QUANTITY_DIFFERENCE
    if price_issue:
        return STATUS_PRICE_DIFFERENCE
    if amt_issue:
        return STATUS_AMOUNT_DIFFERENCE

    if identity == IDENTITY_SUBSTITUTE:
        return STATUS_MATCHED_WITH_SUBSTITUTE

    return STATUS_MATCHED


def reconcile(
    match_results: pd.DataFrame,
    a_lines: pd.DataFrame,
    b_lines: pd.DataFrame,
    a_headers: pd.DataFrame,
    b_headers: pd.DataFrame,
) -> pd.DataFrame:
    """Run reconciliation on match results.

    For each row in *match_results*, compute component statuses and
    the overall reconciliation status.
    """
    # Build lookups
    a_line_map = {row["line_id"]: row for _, row in a_lines.iterrows()}
    b_line_map = {row["line_id"]: row for _, row in b_lines.iterrows()}
    a_header_map = {row["transaction_id"]: row for _, row in a_headers.iterrows()}
    b_header_map = {row["transaction_id"]: row for _, row in b_headers.iterrows()}

    results: list[dict[str, Any]] = []

    for _, mrow in match_results.iterrows():
        a_lid = mrow["source_a_line_id"]
        b_lid = mrow["source_b_line_id"]
        method = mrow["match_method"]
        confidence = mrow["confidence_score"]

        a_line = a_line_map.get(a_lid, {})
        b_line = b_line_map.get(b_lid, {})

        a_txn_id = a_line.get("transaction_id", "")
        b_txn_id = b_line.get("transaction_id", "")

        a_header = a_header_map.get(a_txn_id, {})
        b_header = b_header_map.get(b_txn_id, {})

        txn_type = a_header.get("transaction_type", TXN_CREDIT if a_line.get("source") == SOURCE_A else "SALE")

        # Identity status
        if not a_lid and b_lid:
            identity = IDENTITY_MISSING_A
        elif a_lid and not b_lid:
            # A line with no B counterpart. If a heuristic match was found
            # (but not consumed), the A line is UNRESOLVED rather than
            # purely missing — a potential match exists but isn't confident.
            if method in (MATCH_GENERIC_STRENGTH, MATCH_POSSIBLE_SUBSTITUTE,
                          MATCH_FUZZY_NAME):
                identity = IDENTITY_UNMATCHED
            else:
                identity = IDENTITY_MISSING_B
        elif method == MATCH_NONE:
            identity = IDENTITY_UNMATCHED
        else:
            identity = _identity_status(method)

        # Component statuses
        qty_a = a_line.get("_qty_float")
        qty_b = b_line.get("_qty_float")
        price_a = a_line.get("_price_float")
        price_b = b_line.get("_price_float")
        amt_a = a_line.get("_amount_float")
        amt_b = b_line.get("_amount_float")

        quantity = _quantity_status(qty_a, qty_b)
        price = _price_status(price_a, price_b)
        amount = _amount_status(amt_a, amt_b)

        is_unmatched_a = not a_lid
        is_unmatched_b = not b_lid

        recon_status = _derive_reconciliation_status(
            identity, quantity, price, amount,
            method, confidence, txn_type,
            is_unmatched_a, is_unmatched_b,
        )

        review_required = "Y" if recon_status in {
            STATUS_MISSING_IN_SOURCE_A, STATUS_MISSING_IN_SOURCE_B,
            STATUS_ADDITIONAL_TRANSACTION, STATUS_ADDITIONAL_ITEM,
            STATUS_QUANTITY_DIFFERENCE, STATUS_PRICE_DIFFERENCE,
            STATUS_AMOUNT_DIFFERENCE, STATUS_QUANTITY_AND_AMOUNT_DIFFERENCE,
            STATUS_FUZZY_MATCH_REVIEW, STATUS_MASTER_DATA_EXCEPTION,
            STATUS_DUPLICATE_KEY, STATUS_DATA_QUALITY_EXCEPTION,
            STATUS_UNRESOLVED, STATUS_MATCHED_WITH_SUBSTITUTE,
        } else "N"

        qty_diff = round(qty_a - qty_b, 4) if qty_a is not None and qty_b is not None else None
        price_diff = round(price_a - price_b, 4) if price_a is not None and price_b is not None else None
        amt_diff = round(amt_a - amt_b, 4) if amt_a is not None and amt_b is not None else None

        results.append({
            "source_a_line_id": a_lid,
            "source_a_transaction_id": a_txn_id,
            "source_b_line_id": b_lid,
            "source_b_transaction_id": b_txn_id,
            "match_method": method,
            "confidence_score": confidence,
            "identity_status": identity,
            "quantity_status": quantity,
            "price_status": price,
            "amount_status": amount,
            "reconciliation_status": recon_status,
            "review_required": review_required,
            "quantity_difference": qty_diff,
            "price_difference": price_diff,
            "amount_difference": amt_diff,
            "source_a_product_id": a_line.get("product_id", ""),
            "source_b_product_id": b_line.get("product_id", ""),
            "source_a_product_name": a_line.get("product_name", ""),
            "source_b_product_name": b_line.get("product_name", ""),
            "source_a_amount": amt_a if amt_a is not None else 0.0,
            "source_b_amount": amt_b if amt_b is not None else 0.0,
            "source_a_quantity": qty_a if qty_a is not None else None,
            "source_b_quantity": qty_b if qty_b is not None else None,
            "source_a_unit_price": price_a if price_a is not None else None,
            "source_b_unit_price": price_b if price_b is not None else None,
        })

    # Also add unmatched Source B lines (those not found in any match result)
    matched_b_ids = set(match_results["source_b_line_id"].tolist())
    for _, brow in b_lines.iterrows():
        blid = brow.get("line_id", "")
        if blid and blid not in matched_b_ids:
            b_txn_id = brow.get("transaction_id", "")
            results.append({
                "source_a_line_id": "",
                "source_a_transaction_id": "",
                "source_b_line_id": blid,
                "source_b_transaction_id": b_txn_id,
                "match_method": MATCH_NONE,
                "confidence_score": 0.0,
                "identity_status": IDENTITY_MISSING_A,
                "quantity_status": QUANTITY_NOT_APPLICABLE,
                "price_status": PRICE_NOT_APPLICABLE,
                "amount_status": AMOUNT_NOT_APPLICABLE,
                "reconciliation_status": STATUS_MISSING_IN_SOURCE_A,
                "review_required": "Y",
                "quantity_difference": None,
                "price_difference": None,
                "amount_difference": None,
                "source_a_product_id": "",
                "source_b_product_id": brow.get("product_id", ""),
                "source_a_product_name": "",
                "source_b_product_name": brow.get("product_name", ""),
            })

    return pd.DataFrame(results)
