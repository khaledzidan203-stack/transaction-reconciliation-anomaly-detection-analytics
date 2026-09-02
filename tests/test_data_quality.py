"""Tests for data quality engine: duplicate detection, numeric validity, master refs."""

from pathlib import Path

import pandas as pd
import pytest
from src.data_quality import (
    check_duplicate_keys,
    check_master_data_reference,
    check_missing_values,
    check_numeric_validity,
    check_well_formed_ids,
    run_data_quality,
)
from src.ingestion import load_csvs
from src.synthetic_data_generator import generate_all


class TestDuplicateDetection:
    def test_detects_duplicate_keys(self):
        df = pd.DataFrame({"id": ["A", "B", "A", "C"]})
        issues: list[dict[str, str]] = []
        check_duplicate_keys(df, "id", "test_table", issues)
        assert len(issues) == 2  # rows 0 and 2 have "A" (keep=False marks both)
        assert all(i["issue_type"] == "DUPLICATE_KEY" for i in issues)

    def test_no_duplicates(self):
        df = pd.DataFrame({"id": ["A", "B", "C"]})
        issues: list[dict[str, str]] = []
        check_duplicate_keys(df, "id", "test_table", issues)
        assert len(issues) == 0


class TestNumericValidity:
    def test_detects_invalid_numeric(self):
        df = pd.DataFrame({"qty": ["5", "N/A", "3"], "_qty_float": [5.0, float("nan"), 3.0]})
        issues: list[dict[str, str]] = []
        check_numeric_validity(df, "qty", "_qty_float", "test", issues)
        assert len(issues) == 1
        assert issues[0]["issue_type"] == "INVALID_NUMERIC"

    def test_valid_numbers_no_issues(self):
        df = pd.DataFrame({"qty": ["5", "3"], "_qty_float": [5.0, 3.0]})
        issues: list[dict[str, str]] = []
        check_numeric_validity(df, "qty", "_qty_float", "test", issues)
        assert len(issues) == 0


class TestWellFormedIds:
    def test_malformed_detected(self):
        df = pd.DataFrame({"product_id": ["PRD-0001", "PRD!01#"]})
        issues: list[dict[str, str]] = []
        check_well_formed_ids(df, "product_id", "test", issues)
        assert len(issues) == 1

    def test_well_formed_no_issues(self):
        df = pd.DataFrame({"product_id": ["PRD0001", "PRD0002"]})
        issues: list[dict[str, str]] = []
        check_well_formed_ids(df, "product_id", "test", issues)
        assert len(issues) == 0


class TestMasterReference:
    def test_orphan_detected(self):
        df = pd.DataFrame({"product_id": ["PRD-0001", "PRD-9999"]})
        issues: list[dict[str, str]] = []
        check_master_data_reference(df, "product_id", {"PRD0001"}, "test", issues)
        assert len(issues) == 1
        assert issues[0]["issue_type"] == "MISSING_MASTER_RECORD"


class TestRunDataQuality:
    def test_dq_issues_from_pipeline(self, tmp_path: Path):
        generate_all(tmp_path)
        ds = load_csvs(tmp_path)
        dq = run_data_quality(ds)
        # Injected scenarios should produce at least some issues
        assert len(dq) > 0
        assert "severity" in dq.columns
