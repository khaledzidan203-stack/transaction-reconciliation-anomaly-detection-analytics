"""Anomaly detection engine: rule-based anomaly flagging.

Applies deterministic rules to identify suspicious patterns in
reconciliation results. Each anomaly has a severity and category.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from .config import (
    ANOMALY_HIGH_AMOUNT_MULTIPLIER,
    ANOMALY_HIGH_QUANTITY_MULTIPLIER,
    ANOMALY_HIGH_RATE_THRESHOLD,
    ANOMALY_LOW_CONFIDENCE_THRESHOLD,
    ANOMALY_PRICE_OUTLIER_MULTIPLIER,
    SEVERITY_CRITICAL,
    SEVERITY_HIGH,
    SEVERITY_LOW,
    SEVERITY_MEDIUM,
    STATUS_DATA_QUALITY_EXCEPTION,
    STATUS_DUPLICATE_KEY,
    STATUS_MASTER_DATA_EXCEPTION,
    STATUS_MISSING_IN_SOURCE_A,
    STATUS_MISSING_IN_SOURCE_B,
    STATUS_UNRESOLVED,
)


def detect_anomalies(
    recon_results: pd.DataFrame,
    product_master: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Apply anomaly detection rules to reconciliation results.

    Returns a DataFrame of anomaly records, one per detected anomaly.
    """
    anomalies: list[dict[str, str]] = []

    # Pre-compute population statistics for amount-based rules
    amounts = pd.to_numeric(recon_results.get("absolute_exposure", pd.Series(dtype=float)), errors="coerce").dropna()
    mean_amount = amounts.mean() if len(amounts) > 0 else 0
    std_amount = amounts.std() if len(amounts) > 1 else 0

    for idx, row in recon_results.iterrows():
        status = row.get("reconciliation_status", "")
        confidence = float(row.get("confidence_score", 0))
        abs_exp = float(row.get("absolute_exposure", 0))

        # Rule 1: High-value outlier
        if mean_amount > 0 and abs_exp > mean_amount * ANOMALY_HIGH_AMOUNT_MULTIPLIER:
            anomalies.append({
                "line_key": row.get("source_a_line_id") or row.get("source_b_line_id", ""),
                "anomaly_type": "HIGH_VALUE_OUTLIER",
                "severity": SEVERITY_HIGH,
                "description": f"Amount {abs_exp:.2f} exceeds {ANOMALY_HIGH_AMOUNT_MULTIPLIER}x population mean {mean_amount:.2f}",
                "reconciliation_status": status,
            })

        # Rule 2: Low confidence match
        if 0 < confidence < ANOMALY_LOW_CONFIDENCE_THRESHOLD:
            anomalies.append({
                "line_key": row.get("source_a_line_id") or row.get("source_b_line_id", ""),
                "anomaly_type": "LOW_CONFIDENCE_MATCH",
                "severity": SEVERITY_MEDIUM,
                "description": f"Match confidence {confidence:.1f} below threshold {ANOMALY_LOW_CONFIDENCE_THRESHOLD}",
                "reconciliation_status": status,
            })

        # Rule 3: Data quality exception
        if status == STATUS_DATA_QUALITY_EXCEPTION:
            anomalies.append({
                "line_key": row.get("source_a_line_id") or row.get("source_b_line_id", ""),
                "anomaly_type": "DATA_QUALITY_FAILURE",
                "severity": SEVERITY_CRITICAL,
                "description": "Data quality check failed on this line",
                "reconciliation_status": status,
            })

        # Rule 4: Master data exception
        if status == STATUS_MASTER_DATA_EXCEPTION:
            anomalies.append({
                "line_key": row.get("source_a_line_id") or row.get("source_b_line_id", ""),
                "anomaly_type": "MASTER_DATA_MISSING",
                "severity": SEVERITY_HIGH,
                "description": "Product not found in master data",
                "reconciliation_status": status,
            })

        # Rule 5: Duplicate key
        if status == STATUS_DUPLICATE_KEY:
            anomalies.append({
                "line_key": row.get("source_a_line_id") or row.get("source_b_line_id", ""),
                "anomaly_type": "DUPLICATE_KEY",
                "severity": SEVERITY_HIGH,
                "description": "Duplicate transaction or line key detected",
                "reconciliation_status": status,
            })

        # Rule 6: Unresolved match
        if status == STATUS_UNRESOLVED:
            anomalies.append({
                "line_key": row.get("source_a_line_id") or row.get("source_b_line_id", ""),
                "anomaly_type": "UNRESOLVED_TRANSACTION",
                "severity": SEVERITY_MEDIUM,
                "description": "No matching path found for this transaction line",
                "reconciliation_status": status,
            })

        # Rule 7: Missing in source (informational)
        if status in (STATUS_MISSING_IN_SOURCE_A, STATUS_MISSING_IN_SOURCE_B):
            anomalies.append({
                "line_key": row.get("source_a_line_id") or row.get("source_b_line_id", ""),
                "anomaly_type": "MISSING_COUNTERPART",
                "severity": SEVERITY_LOW,
                "description": f"Status: {status}",
                "reconciliation_status": status,
            })

    return pd.DataFrame(anomalies) if anomalies else pd.DataFrame(
        columns=["line_key", "anomaly_type", "severity", "description", "reconciliation_status"]
    )
