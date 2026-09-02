"""Tests for src.config: validate all constants are defined and consistent."""

import pytest
from src.config import (
    AMOUNT_TOLERANCE,
    CONFIDENCE_BARCODE,
    CONFIDENCE_GENERIC_STRENGTH,
    CONFIDENCE_NORMALIZED_NAME,
    CONFIDENCE_POSSIBLE_SUBSTITUTE,
    CONFIDENCE_PRIMARY_ID,
    CONFIDENCE_PRODUCT_CODE,
    CONFIDENCE_UNMATCHED,
    EXCEPTION_STATUSES,
    FUZZY_ACCEPT_THRESHOLD,
    FUZZY_REVIEW_THRESHOLD,
    MATCH_EXACT_BARCODE,
    MATCH_EXACT_PRIMARY_ID,
    MATCH_EXACT_PRODUCT_CODE,
    MATCH_FUZZY_NAME,
    MATCH_GENERIC_STRENGTH,
    MATCH_METHOD_HIERARCHY,
    MATCH_NONE,
    MATCH_NORMALIZED_NAME,
    MATCH_POSSIBLE_SUBSTITUTE,
    N_BASE_TRANSACTIONS,
    N_BRANCHES,
    N_EMPLOYEES,
    N_PRODUCTS,
    QUANTITY_TOLERANCE,
    RANDOM_SEED,
    RECONCILIATION_STATUSES,
    REVIEW_CONFIDENCE_FLOOR,
    ROUNDING_DECIMALS,
    SCENARIO_COUNTS,
    SCENARIO_TYPES,
    SOURCE_A,
    SOURCE_B,
    UNIT_PRICE_TOLERANCE,
)


class TestConstants:
    def test_random_seed_is_deterministic(self):
        assert RANDOM_SEED == 20260902

    def test_dataset_scale_positive(self):
        assert N_BRANCHES > 0
        assert N_EMPLOYEES > 0
        assert N_PRODUCTS > 0
        assert N_BASE_TRANSACTIONS > 0

    def test_source_labels_distinct(self):
        assert SOURCE_A != SOURCE_B

    def test_match_hierarchy_complete(self):
        expected = {
            MATCH_EXACT_PRIMARY_ID, MATCH_EXACT_BARCODE, MATCH_EXACT_PRODUCT_CODE,
            MATCH_NORMALIZED_NAME, MATCH_FUZZY_NAME, MATCH_GENERIC_STRENGTH,
            MATCH_POSSIBLE_SUBSTITUTE, MATCH_NONE,
        }
        assert set(MATCH_METHOD_HIERARCHY) == expected
        assert len(MATCH_METHOD_HIERARCHY) == 8

    def test_match_hierarchy_order(self):
        assert MATCH_METHOD_HIERARCHY[0] == MATCH_EXACT_PRIMARY_ID
        assert MATCH_METHOD_HIERARCHY[-1] == MATCH_NONE

    def test_confidence_scores_ordered(self):
        scores = [
            CONFIDENCE_PRIMARY_ID, CONFIDENCE_BARCODE, CONFIDENCE_PRODUCT_CODE,
            CONFIDENCE_NORMALIZED_NAME, CONFIDENCE_GENERIC_STRENGTH,
            CONFIDENCE_POSSIBLE_SUBSTITUTE, CONFIDENCE_UNMATCHED,
        ]
        for i in range(len(scores) - 1):
            assert scores[i] > scores[i + 1]

    def test_fuzzy_thresholds(self):
        assert 0 < FUZZY_REVIEW_THRESHOLD < FUZZY_ACCEPT_THRESHOLD <= 1.0

    def test_tolerances_non_negative(self):
        assert UNIT_PRICE_TOLERANCE >= 0
        assert AMOUNT_TOLERANCE >= 0
        assert QUANTITY_TOLERANCE >= 0

    def test_reconciliation_statuses_defined(self):
        assert len(RECONCILIATION_STATUSES) == 17
        assert "MATCHED" in RECONCILIATION_STATUSES
        assert "UNRESOLVED" in RECONCILIATION_STATUSES

    def test_exception_statuses_subset(self):
        assert EXCEPTION_STATUSES < set(RECONCILIATION_STATUSES)
        assert "MATCHED" not in EXCEPTION_STATUSES

    def test_scenario_types_match_counts_keys(self):
        assert set(SCENARIO_TYPES) == set(SCENARIO_COUNTS.keys())

    def test_scenario_counts_positive(self):
        for stype, count in SCENARIO_COUNTS.items():
            assert count > 0, f"SCENARIO_COUNTS[{stype}] must be > 0"

    def test_review_confidence_floor_in_range(self):
        assert 0 < REVIEW_CONFIDENCE_FLOOR <= 100

    def test_rounding_decimals_positive(self):
        assert ROUNDING_DECIMALS > 0
