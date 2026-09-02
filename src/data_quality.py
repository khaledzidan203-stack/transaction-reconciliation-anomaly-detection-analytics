"""Data quality engine: detect errors, warnings and business anomalies.

Runs a battery of deterministic checks against source data and produces
a structured issues table consumed by the reconciliation pipeline and
the review queue.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from .config import (
    DQ_BUSINESS_ANOMALY,
    DQ_ERROR,
    DQ_WARNING,
    SOURCE_A,
    SOURCE_B,
)
from .normalization import is_well_formed_identifier, normalize_identifier


def _add_issue(
    issues: list[dict[str, str]],
    table: str, field: str, issue_type: str, severity: str,
    description: str, record_key: str,
) -> None:
    issues.append({
        "table": table,
        "field": field,
        "issue_type": issue_type,
        "severity": severity,
        "description": description,
        "record_key": record_key,
    })


def check_duplicate_keys(
    frame: pd.DataFrame, key_col: str, table_name: str,
    issues: list[dict[str, str]],
) -> None:
    """Flag duplicate values in *key_col*."""
    dup_mask = frame[key_col].duplicated(keep=False)
    for idx in frame.loc[dup_mask].index:
        val = frame.at[idx, key_col]
        _add_issue(issues, table_name, key_col, "DUPLICATE_KEY", DQ_ERROR,
                   f"Duplicate {key_col} value: {val}", str(val))


def check_well_formed_ids(
    frame: pd.DataFrame, col: str, table_name: str,
    issues: list[dict[str, str]],
) -> None:
    """Flag malformed identifiers."""
    for idx in frame.index:
        val = frame.at[idx, col]
        if val and not is_well_formed_identifier(val):
            _add_issue(issues, table_name, col, "MALFORMED_IDENTIFIER", DQ_ERROR,
                       f"Identifier '{val}' is not well formed", str(val))


def check_numeric_validity(
    frame: pd.DataFrame, col: str, float_col: str, table_name: str,
    issues: list[dict[str, str]],
) -> None:
    """Flag rows where a text numeric cannot be parsed."""
    mask = frame[col].notna() & (frame[col] != "") & frame[float_col].isna()
    for idx in frame.loc[mask].index:
        val = frame.at[idx, col]
        _add_issue(issues, table_name, col, "INVALID_NUMERIC", DQ_ERROR,
                   f"Non-numeric value '{val}' in {col}", str(val))


def check_missing_values(
    frame: pd.DataFrame, required_cols: list[str], table_name: str,
    issues: list[dict[str, str]],
) -> None:
    """Flag missing or empty required fields."""
    for col in required_cols:
        mask = frame[col].isna() | (frame[col] == "")
        for idx in frame.loc[mask].index:
            key = frame.at[idx, frame.columns[0]] if len(frame.columns) > 0 else ""
            _add_issue(issues, table_name, col, "MISSING_VALUE", DQ_ERROR,
                       f"Missing required value in {col}", str(key))


def check_master_data_reference(
    frame: pd.DataFrame, key_col: str, master_ids: set[str],
    table_name: str, issues: list[dict[str, str]],
) -> None:
    """Flag transaction lines referencing products not in master data."""
    for idx in frame.index:
        val = normalize_identifier(frame.at[idx, key_col])
        if val and val not in master_ids:
            raw = frame.at[idx, key_col]
            _add_issue(issues, table_name, key_col, "MISSING_MASTER_RECORD",
                       DQ_BUSINESS_ANOMALY,
                       f"Product '{raw}' not found in master data", str(raw))


def run_data_quality(dataset: Any) -> pd.DataFrame:
    """Execute all data quality checks against the loaded dataset.

    Returns a DataFrame of issues.
    """
    issues: list[dict[str, str]] = []

    # Duplicate checks
    check_duplicate_keys(dataset.source_a_headers, "transaction_id", "source_a_headers", issues)
    check_duplicate_keys(dataset.source_b_headers, "transaction_id", "source_b_headers", issues)
    check_duplicate_keys(dataset.source_a_lines, "line_id", "source_a_lines", issues)
    check_duplicate_keys(dataset.source_b_lines, "line_id", "source_b_lines", issues)

    # Identifier format checks
    check_well_formed_ids(dataset.source_a_lines, "product_id", "source_a_lines", issues)
    check_well_formed_ids(dataset.source_b_lines, "product_id", "source_b_lines", issues)

    # Numeric validity checks
    for frame, table in [
        (dataset.source_a_lines, "source_a_lines"),
        (dataset.source_b_lines, "source_b_lines"),
    ]:
        check_numeric_validity(frame, "quantity", "_qty_float", table, issues)
        check_numeric_validity(frame, "unit_price", "_price_float", table, issues)
        check_numeric_validity(frame, "amount", "_amount_float", table, issues)

    # Master data reference checks
    master_ids = set(
        dataset.product_master["product_id"].map(normalize_identifier)
    )
    check_master_data_reference(
        dataset.source_a_lines, "product_id", master_ids, "source_a_lines", issues)
    check_master_data_reference(
        dataset.source_b_lines, "product_id", master_ids, "source_b_lines", issues)

    return pd.DataFrame(issues) if issues else pd.DataFrame(
        columns=["table", "field", "issue_type", "severity", "description", "record_key"]
    )
