"""Review queue: prioritize reconciliation exceptions for manual review.

Assigns priority based on reconciliation status, exposure amount and
anomaly severity so that reviewers can focus on the highest-impact items.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from .config import (
    PRIORITY_CRITICAL,
    PRIORITY_HIGH,
    PRIORITY_LOW,
    PRIORITY_MEDIUM,
    SEVERITY_CRITICAL,
    SEVERITY_HIGH,
    STATUS_DATA_QUALITY_EXCEPTION,
    STATUS_DUPLICATE_KEY,
    STATUS_MASTER_DATA_EXCEPTION,
    STATUS_MISSING_IN_SOURCE_A,
    STATUS_MISSING_IN_SOURCE_B,
    STATUS_UNRESOLVED,
)


def _priority_from_status(status: str, exposure: float) -> str:
    """Map reconciliation status and exposure to a review priority."""
    if status in (STATUS_DATA_QUALITY_EXCEPTION, STATUS_DUPLICATE_KEY):
        return PRIORITY_CRITICAL
    if status in (STATUS_MASTER_DATA_EXCEPTION, STATUS_UNRESOLVED):
        return PRIORITY_HIGH if exposure > 1000 else PRIORITY_MEDIUM
    if status in (STATUS_MISSING_IN_SOURCE_A, STATUS_MISSING_IN_SOURCE_B):
        return PRIORITY_HIGH if exposure > 500 else PRIORITY_MEDIUM
    return PRIORITY_LOW


def build_review_queue(
    recon_results: pd.DataFrame,
    anomaly_results: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Build a prioritized review queue from reconciliation results.

    Only rows with ``review_required == 'Y'`` are included.
    """
    mask = recon_results.get("review_required", pd.Series(dtype=str)) == "Y"
    review_items = recon_results.loc[mask].copy()

    if review_items.empty:
        return pd.DataFrame(columns=[
            "line_key", "priority", "reconciliation_status", "match_method",
            "confidence_score", "absolute_exposure", "anomaly_flags",
        ])

    # Map anomaly severities to each line
    anomaly_map: dict[str, list[str]] = {}
    if anomaly_results is not None and not anomaly_results.empty:
        for _, arow in anomaly_results.iterrows():
            key = arow.get("line_key", "")
            atype = arow.get("anomaly_type", "")
            anomaly_map.setdefault(key, []).append(atype)

    rows: list[dict[str, Any]] = []
    for _, rrow in review_items.iterrows():
        line_key = rrow.get("source_a_line_id") or rrow.get("source_b_line_id", "")
        status = rrow.get("reconciliation_status", "")
        exposure = float(rrow.get("absolute_exposure", 0))
        priority = _priority_from_status(status, exposure)

        # Upgrade priority if a CRITICAL anomaly is attached
        if anomaly_map.get(line_key):
            if SEVERITY_CRITICAL in [a for a in anomaly_map[line_key]]:
                priority = PRIORITY_CRITICAL

        rows.append({
            "line_key": line_key,
            "priority": priority,
            "reconciliation_status": status,
            "match_method": rrow.get("match_method", ""),
            "confidence_score": rrow.get("confidence_score", 0),
            "absolute_exposure": exposure,
            "anomaly_flags": ";".join(anomaly_map.get(line_key, [])),
        })

    df = pd.DataFrame(rows)
    # Sort by priority (CRITICAL > HIGH > MEDIUM > LOW) then exposure descending
    priority_order = {PRIORITY_CRITICAL: 0, PRIORITY_HIGH: 1, PRIORITY_MEDIUM: 2, PRIORITY_LOW: 3}
    df["_prio_sort"] = df["priority"].map(priority_order).fillna(4)
    df.sort_values(["_prio_sort", "absolute_exposure"], ascending=[True, False], inplace=True)
    df.drop(columns=["_prio_sort"], inplace=True)
    df.reset_index(drop=True, inplace=True)

    return df
