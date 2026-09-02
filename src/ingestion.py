"""Data ingestion: load raw CSV files into typed DataFrames.

Reads all source files produced by the synthetic generator, applies
normalization and numeric parsing, and returns a single namespace object
so downstream modules never touch the filesystem directly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from .config import (
    DATA_DIR,
    FILE_BRANCH_MASTER,
    FILE_EMPLOYEE_MASTER,
    FILE_EXPECTED_SCENARIOS,
    FILE_PRODUCT_MASTER,
    FILE_SOURCE_A_HEADERS,
    FILE_SOURCE_A_LINES,
    FILE_SOURCE_B_HEADERS,
    FILE_SOURCE_B_LINES,
    SAMPLE_DIR,
    SOURCE_A,
    SOURCE_B,
)
from .normalization import (
    normalize_barcode,
    normalize_identifier,
    normalize_product_name,
    parse_amount,
    parse_price,
    parse_quantity,
    to_float_series,
)
from .utils import read_csv


@dataclass
class RawDataset:
    """Container for all loaded and lightly typed DataFrames."""

    product_master: pd.DataFrame = field(default_factory=pd.DataFrame)
    branch_master: pd.DataFrame = field(default_factory=pd.DataFrame)
    employee_master: pd.DataFrame = field(default_factory=pd.DataFrame)
    source_a_headers: pd.DataFrame = field(default_factory=pd.DataFrame)
    source_a_lines: pd.DataFrame = field(default_factory=pd.DataFrame)
    source_b_headers: pd.DataFrame = field(default_factory=pd.DataFrame)
    source_b_lines: pd.DataFrame = field(default_factory=pd.DataFrame)
    expected_scenarios: pd.DataFrame = field(default_factory=pd.DataFrame)


def load_csvs(data_dir: Any = None) -> RawDataset:
    """Load all raw CSVs and return a typed dataset container.

    Parameters
    ----------
    data_dir:
        Directory containing the CSV files. Defaults to ``SAMPLE_DIR``.
    """
    base = data_dir or SAMPLE_DIR

    ds = RawDataset(
        product_master=read_csv(base / FILE_PRODUCT_MASTER),
        branch_master=read_csv(base / FILE_BRANCH_MASTER),
        employee_master=read_csv(base / FILE_EMPLOYEE_MASTER),
        source_a_headers=read_csv(base / FILE_SOURCE_A_HEADERS),
        source_a_lines=read_csv(base / FILE_SOURCE_A_LINES),
        source_b_headers=read_csv(base / FILE_SOURCE_B_HEADERS),
        source_b_lines=read_csv(base / FILE_SOURCE_B_LINES),
        expected_scenarios=read_csv(base / FILE_EXPECTED_SCENARIOS),
    )

    # Add normalized key columns to source lines for matching
    for frame, source_label in [
        (ds.source_a_lines, SOURCE_A),
        (ds.source_b_lines, SOURCE_B),
    ]:
        frame["_source"] = source_label
        frame["_norm_product_name"] = frame["product_name"].map(normalize_product_name)
        frame["_norm_barcode"] = frame["barcode"].map(normalize_barcode)
        frame["_norm_product_code"] = frame["product_code"].map(
            lambda v: normalize_identifier(v)
        )
        frame["_norm_reference_id"] = frame["reference_id"].map(
            lambda v: normalize_identifier(v)
        )
        frame["_norm_txn_id"] = frame["transaction_id"].map(normalize_identifier)
        frame["_qty_float"] = to_float_series(frame["quantity"], parse_quantity)
        frame["_price_float"] = to_float_series(frame["unit_price"], parse_price)
        frame["_amount_float"] = to_float_series(frame["amount"], parse_amount)

    # Parse reference_unit_price on product master
    ds.product_master["_ref_price_float"] = to_float_series(
        ds.product_master["reference_unit_price"], parse_price
    )

    return ds
