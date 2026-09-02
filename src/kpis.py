"""KPI framework: compute reconciliation performance metrics.

Produces summary KPIs, KPIs by branch and by month for dashboard
consumption and trend analysis.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from .config import (
    EXCEPTION_STATUSES,
    STATUS_MATCHED,
    STATUS_MATCHED_WITH_SUBSTITUTE,
)


def _total_lines(recon: pd.DataFrame) -> int:
    return len(recon)


def _matched_lines(recon: pd.DataFrame) -> int:
    return int(((recon["reconciliation_status"] == STATUS_MATCHED) |
                (recon["reconciliation_status"] == STATUS_MATCHED_WITH_SUBSTITUTE)).sum())


def _exception_lines(recon: pd.DataFrame) -> int:
    return int(recon["reconciliation_status"].isin(EXCEPTION_STATUSES).sum())


def _total_exposure(recon: pd.DataFrame) -> float:
    col = "absolute_exposure" if "absolute_exposure" in recon.columns else "amount_difference"
    return float(pd.to_numeric(recon[col], errors="coerce").fillna(0).sum())


def _unresolved_exposure(recon: pd.DataFrame) -> float:
    if "unresolved_exposure" not in recon.columns:
        return 0.0
    return float(pd.to_numeric(recon["unresolved_exposure"], errors="coerce").fillna(0).sum())


def _avg_confidence(recon: pd.DataFrame) -> float:
    return float(pd.to_numeric(recon["confidence_score"], errors="coerce").mean())


def _review_count(recon: pd.DataFrame) -> int:
    return int((recon.get("review_required", pd.Series(dtype=str)) == "Y").sum())


def compute_kpis(recon: pd.DataFrame) -> dict[str, Any]:
    """Compute top-level reconciliation KPIs."""
    total = _total_lines(recon)
    matched = _matched_lines(recon)
    exceptions = _exception_lines(recon)
    match_rate = (matched / total * 100) if total > 0 else 0.0
    exception_rate = (exceptions / total * 100) if total > 0 else 0.0
    review_pct = (_review_count(recon) / total * 100) if total > 0 else 0.0

    return {
        "total_lines": total,
        "matched_lines": matched,
        "exception_lines": exceptions,
        "match_rate_pct": round(match_rate, 2),
        "exception_rate_pct": round(exception_rate, 2),
        "total_absolute_exposure": round(_total_exposure(recon), 2),
        "unresolved_exposure": round(_unresolved_exposure(recon), 2),
        "average_confidence": round(_avg_confidence(recon), 2),
        "review_required_count": _review_count(recon),
        "review_rate_pct": round(review_pct, 2),
    }


def compute_kpis_by_branch(
    recon: pd.DataFrame, a_headers: pd.DataFrame, b_headers: pd.DataFrame,
) -> pd.DataFrame:
    """Compute KPIs broken down by branch."""
    # Merge branch_id from headers onto recon results
    a_map = dict(zip(a_headers["transaction_id"], a_headers["branch_id"]))
    b_map = dict(zip(b_headers["transaction_id"], b_headers["branch_id"]))

    recon_copy = recon.copy()
    recon_copy["branch_id"] = recon_copy["source_a_transaction_id"].map(a_map)
    mask_null = recon_copy["branch_id"].isna() | (recon_copy["branch_id"] == "")
    recon_copy.loc[mask_null, "branch_id"] = recon_copy.loc[mask_null, "source_b_transaction_id"].map(b_map)
    recon_copy["branch_id"] = recon_copy["branch_id"].fillna("UNKNOWN")

    rows = []
    for branch, group in recon_copy.groupby("branch_id"):
        kpis = compute_kpis(group)
        kpis["branch_id"] = branch
        rows.append(kpis)

    return pd.DataFrame(rows) if rows else pd.DataFrame()


def compute_kpis_by_month(
    recon: pd.DataFrame, a_headers: pd.DataFrame, b_headers: pd.DataFrame,
) -> pd.DataFrame:
    """Compute KPIs broken down by month."""
    from .normalization import date_key

    a_map = dict(zip(a_headers["transaction_id"], a_headers["transaction_date"]))
    b_map = dict(zip(b_headers["transaction_id"], b_headers["transaction_date"]))

    recon_copy = recon.copy()
    recon_copy["_date"] = recon_copy["source_a_transaction_id"].map(a_map)
    mask_null = recon_copy["_date"].isna() | (recon_copy["_date"] == "")
    recon_copy.loc[mask_null, "_date"] = recon_copy.loc[mask_null, "source_b_transaction_id"].map(b_map)
    recon_copy["month_key"] = recon_copy["_date"].map(date_key)
    recon_copy["month_key"] = recon_copy["month_key"].fillna("UNKNOWN")

    rows = []
    for month, group in recon_copy.groupby("month_key"):
        kpis = compute_kpis(group)
        kpis["month_key"] = month
        rows.append(kpis)

    return pd.DataFrame(rows) if rows else pd.DataFrame()
