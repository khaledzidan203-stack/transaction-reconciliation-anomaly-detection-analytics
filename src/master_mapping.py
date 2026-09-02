"""Master data mapping: build lookup dictionaries from master tables.

Provides fast access to product, branch and employee reference data
so that the matching and reconciliation engines never scan full tables.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from .normalization import normalize_barcode, normalize_identifier, normalize_product_name


@dataclass
class MasterMaps:
    """Pre-built lookup structures derived from master data."""

    product_by_id: dict[str, dict[str, str]] = field(default_factory=dict)
    product_by_barcode: dict[str, dict[str, str]] = field(default_factory=dict)
    product_by_code: dict[str, dict[str, str]] = field(default_factory=dict)
    product_by_norm_name: dict[str, list[dict[str, str]]] = field(default_factory=dict)
    product_by_generic: dict[str, list[dict[str, str]]] = field(default_factory=dict)
    branch_by_id: dict[str, dict[str, str]] = field(default_factory=dict)
    employee_by_id: dict[str, dict[str, str]] = field(default_factory=dict)


def build_master_maps(dataset: Any) -> MasterMaps:
    """Build lookup dictionaries from master tables.

    Parameters
    ----------
    dataset:
        A ``RawDataset`` with ``product_master``, ``branch_master``
        and ``employee_master`` DataFrames.
    """
    maps = MasterMaps()

    # Product lookups
    for _, row in dataset.product_master.iterrows():
        rec = row.to_dict()
        pid = normalize_identifier(row["product_id"])
        maps.product_by_id[pid] = rec

        bc = normalize_barcode(row["barcode"])
        if bc:
            maps.product_by_barcode[bc] = rec

        code = normalize_identifier(row["product_code"])
        if code:
            maps.product_by_code[code] = rec

        norm_name = normalize_product_name(row["product_name"])
        maps.product_by_norm_name.setdefault(norm_name, []).append(rec)

        generic = row.get("generic_name", "")
        if generic:
            norm_generic = normalize_product_name(generic)
            maps.product_by_generic.setdefault(norm_generic, []).append(rec)

    # Branch lookup
    for _, row in dataset.branch_master.iterrows():
        bid = normalize_identifier(row["branch_id"])
        maps.branch_by_id[bid] = row.to_dict()

    # Employee lookup
    for _, row in dataset.employee_master.iterrows():
        eid = normalize_identifier(row["employee_id"])
        maps.employee_by_id[eid] = row.to_dict()

    return maps
