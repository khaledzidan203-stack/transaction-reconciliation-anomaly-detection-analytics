"""Tests for matching engine: hierarchy correctness and confidence scores."""

from pathlib import Path

import pandas as pd
import pytest
from src.config import (
    CONFIDENCE_PRIMARY_ID,
    CONFIDENCE_UNMATCHED,
    MATCH_EXACT_BARCODE,
    MATCH_EXACT_PRIMARY_ID,
    MATCH_EXACT_PRODUCT_CODE,
    MATCH_FUZZY_NAME,
    MATCH_NONE,
    MATCH_NORMALIZED_NAME,
    SOURCE_A,
    SOURCE_B,
)
from src.ingestion import load_csvs
from src.matching import match_lines
from src.synthetic_data_generator import generate_all


class TestMatchingHierarchy:
    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path: Path):
        generate_all(tmp_path)
        self.ds = load_csvs(tmp_path)

    def test_match_results_has_expected_columns(self):
        result = match_lines(self.ds.source_a_lines, self.ds.source_b_lines)
        required = {"source_a_line_id", "match_method", "confidence_score"}
        assert required <= set(result.columns)

    def test_primary_id_matches_found(self):
        result = match_lines(self.ds.source_a_lines, self.ds.source_b_lines)
        methods = set(result["match_method"].unique())
        assert MATCH_EXACT_PRIMARY_ID in methods

    def test_unmatched_lines_exist(self):
        result = match_lines(self.ds.source_a_lines, self.ds.source_b_lines)
        unmatched = result[result["match_method"] == MATCH_NONE]
        assert len(unmatched) > 0

    def test_confidence_primary_id_is_highest(self):
        result = match_lines(self.ds.source_a_lines, self.ds.source_b_lines)
        primary = result[result["match_method"] == MATCH_EXACT_PRIMARY_ID]
        if len(primary) > 0:
            assert all(primary["confidence_score"] == CONFIDENCE_PRIMARY_ID)

    def test_unmatched_confidence_is_zero(self):
        result = match_lines(self.ds.source_a_lines, self.ds.source_b_lines)
        unmatched = result[result["match_method"] == MATCH_NONE]
        if len(unmatched) > 0:
            assert all(unmatched["confidence_score"] == CONFIDENCE_UNMATCHED)

    def test_each_a_line_produces_one_result(self):
        result = match_lines(self.ds.source_a_lines, self.ds.source_b_lines)
        assert len(result) == len(self.ds.source_a_lines)
