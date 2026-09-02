"""Exposure analysis: quantify financial impact of reconciliation discrepancies.

Computes signed and absolute exposure for every reconciliation result,
broken down by category (quantity, price, amount, unresolved, review).
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from .config import (
    EXCEPTION_STATUSES,
    STATUS_MISSING_IN_SOURCE_A,
    STATUS_MISSING_IN_SOURCE_B,
    STATUS_UNRESOLVED,
)


def compute_exposure(recon_results: pd.DataFrame) -> pd.DataFrame:
    """Add exposure columns to reconciliation results.

    Exposure methodology:
    - signed_exposure: (Source A amount - Source B amount)
    - absolute_exposure: |signed_exposure|
    - quantity_exposure: value of quantity difference at Source B unit price
    - price_exposure: value of price difference at Source A quantity
    - amount_exposure: residual after accounting for qty and price
    - unresolved_exposure: full Source A amount where UNRESOLVED
    - review_exposure: full amount where review_required = Y
    """
    df = recon_results.copy()

    # Build source A and B amount columns from what is available
    if "source_a_amount" in df.columns:
        df["_amt_a"] = pd.to_numeric(df["source_a_amount"], errors="coerce").fillna(0)
    else:
        df["_amt_a"] = 0.0
        df["source_a_amount"] = 0.0

    if "source_b_amount" in df.columns:
        df["_amt_b"] = pd.to_numeric(df["source_b_amount"], errors="coerce").fillna(0)
    else:
        df["_amt_b"] = 0.0
        df["source_b_amount"] = 0.0

    # Signed and absolute exposure
    df["signed_exposure"] = df["_amt_a"] - df["_amt_b"]
    df["absolute_exposure"] = df["signed_exposure"].abs()

    # Quantity exposure
    qty_diff = pd.to_numeric(df.get("quantity_difference"), errors="coerce").fillna(0)
    price_b = pd.to_numeric(df.get("source_b_unit_price"), errors="coerce").fillna(0)
    df["quantity_exposure"] = (qty_diff * price_b).abs()

    # Price exposure
    price_diff = pd.to_numeric(df.get("price_difference"), errors="coerce").fillna(0)
    qty_a = pd.to_numeric(df.get("source_a_quantity"), errors="coerce").fillna(0)
    df["price_exposure"] = (price_diff * qty_a).abs()

    # Amount exposure (residual)
    df["amount_exposure"] = (df["absolute_exposure"] - df["quantity_exposure"] - df["price_exposure"]).clip(lower=0)

    # Unresolved exposure: full amount for UNRESOLVED lines
    df["unresolved_exposure"] = 0.0
    mask_unresolved = df["reconciliation_status"] == STATUS_UNRESOLVED
    df.loc[mask_unresolved, "unresolved_exposure"] = df.loc[mask_unresolved, "_amt_a"]

    # Missing-in-source exposure
    mask_missing_a = df["reconciliation_status"] == STATUS_MISSING_IN_SOURCE_A
    df.loc[mask_missing_a, "unresolved_exposure"] = df.loc[mask_missing_a, "_amt_b"]

    mask_missing_b = df["reconciliation_status"] == STATUS_MISSING_IN_SOURCE_B
    df.loc[mask_missing_b, "unresolved_exposure"] = df.loc[mask_missing_b, "_amt_a"]

    # Review exposure
    df["review_exposure"] = 0.0
    mask_review = df["review_required"] == "Y"
    df.loc[mask_review, "review_exposure"] = df.loc[mask_review, "absolute_exposure"]

    # Cleanup temp columns
    df.drop(columns=["_amt_a", "_amt_b"], inplace=True)

    return df


def exposure_summary(recon_with_exposure: pd.DataFrame) -> pd.DataFrame:
    """Aggregate exposure by reconciliation status."""
    return recon_with_exposure.groupby("reconciliation_status").agg(
        count=("reconciliation_status", "size"),
        total_signed_exposure=("signed_exposure", "sum"),
        total_absolute_exposure=("absolute_exposure", "sum"),
        total_unresolved_exposure=("unresolved_exposure", "sum"),
        total_review_exposure=("review_exposure", "sum"),
    ).reset_index()
