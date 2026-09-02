"""Schema validation: verify loaded CSVs conform to expected column structure.

Each check produces a row in the data quality issues table so that schema
drift is tracked alongside content quality problems.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from .config import DQ_ERROR, DQ_WARNING


# Expected columns for each input table.
EXPECTED_COLUMNS: dict[str, list[str]] = {
    "product_master": [
        "product_id", "product_code", "barcode", "product_name",
        "generic_name", "brand", "category", "strength",
        "reference_unit_price",
    ],
    "branch_master": ["branch_id", "branch_name", "city", "region"],
    "employee_master": ["employee_id", "employee_label", "branch_id"],
    "source_a_headers": [
        "transaction_id", "branch_id", "employee_id",
        "transaction_date", "transaction_type", "total_amount", "source",
    ],
    "source_a_lines": [
        "line_id", "transaction_id", "product_id", "product_code",
        "barcode", "product_name", "generic_name", "quantity",
        "unit_price", "amount", "reference_id", "source",
    ],
    "source_b_headers": [
        "transaction_id", "branch_id", "employee_id",
        "transaction_date", "transaction_type", "total_amount", "source",
    ],
    "source_b_lines": [
        "line_id", "transaction_id", "product_id", "product_code",
        "barcode", "product_name", "generic_name", "quantity",
        "unit_price", "amount", "reference_id", "source",
    ],
}


def validate_schema(
    frame: pd.DataFrame, table_name: str, issues: list[dict[str, str]] | None = None,
) -> list[dict[str, str]]:
    """Validate that *frame* has all expected columns for *table_name*.

    Returns a list of issue dictionaries (and appends to *issues* if given).
    """
    if issues is None:
        issues = []

    expected = EXPECTED_COLUMNS.get(table_name)
    if expected is None:
        return issues

    actual = set(frame.columns)
    missing = [c for c in expected if c not in actual]
    extra = [c for c in actual if c not in set(expected) and not c.startswith("_")]

    for col in missing:
        issues.append({
            "table": table_name,
            "field": col,
            "issue_type": "MISSING_COLUMN",
            "severity": DQ_ERROR,
            "description": f"Required column '{col}' is missing from {table_name}",
            "record_key": "",
        })

    for col in extra:
        issues.append({
            "table": table_name,
            "field": col,
            "issue_type": "UNEXPECTED_COLUMN",
            "severity": DQ_WARNING,
            "description": f"Unexpected column '{col}' in {table_name}",
            "record_key": "",
        })

    return issues


def validate_all_schemas(dataset: Any) -> pd.DataFrame:
    """Run schema validation across every table in the dataset.

    Parameters
    ----------
    dataset:
        A ``RawDataset`` instance.

    Returns
    -------
    pd.DataFrame
        Data quality issues found during schema validation.
    """
    issues: list[dict[str, str]] = []

    validate_schema(dataset.product_master, "product_master", issues)
    validate_schema(dataset.branch_master, "branch_master", issues)
    validate_schema(dataset.employee_master, "employee_master", issues)
    validate_schema(dataset.source_a_headers, "source_a_headers", issues)
    validate_schema(dataset.source_a_lines, "source_a_lines", issues)
    validate_schema(dataset.source_b_headers, "source_b_headers", issues)
    validate_schema(dataset.source_b_lines, "source_b_lines", issues)

    return pd.DataFrame(issues) if issues else pd.DataFrame()
