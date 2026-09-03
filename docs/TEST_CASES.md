# Test Cases

## Overview

The automated test suite validates the reconciliation analytics pipeline across all modules. Tests are organized by module and run via `pytest tests/ -v`.

---

## Test Categories

| Category | Test File | Focus |
|---|---|---|
| Configuration | `test_config.py` | Constants, consistency, ordering |
| Utilities | `test_utils.py` | Deterministic IO, rounding, hashing |
| Normalization | `test_normalization.py` | Text/identifier/numeric normalizers |
| Synthetic Data | `test_synthetic_data.py` | Generator determinism, data structure |
| Data Quality | `test_data_quality.py` | DQ checks: duplicates, IDs, numerics, master refs |
| Matching | `test_matching.py` | Hierarchy correctness, confidence scores |
| Reconciliation & Integration | `test_reconciliation.py` | Statuses, exposure, anomalies, KPIs, review queue |
| Pipeline | `test_pipeline.py` | End-to-end integration, ground truth regression |

---

## Test Coverage Summary

| Module | Test Classes | Test Methods | Key Scenarios Covered |
|---|---|---|---|
| `config.py` | `TestConstants` | 12 | Seed determinism, hierarchy completeness, confidence ordering, threshold validity, status count |
| `utils.py` | `TestRoundMoney`, `TestCsvIO`, `TestJsonIO`, `TestDescribeFrame`, `TestIterSorted` | 12 | Rounding, CSV roundtrip, hash determinism, JSON sorted keys, frame fingerprint |
| `normalization.py` | `TestNormalizeUnicode`, `TestNormalizeNull`, `TestNormalizeWhitespace`, `TestNormalizePunctuation`, `TestNormalizeHyphensSlashes`, `TestStripSeparators`, `TestIdentifiers`, `TestEAN13`, `TestNormalizeStrength`, `TestNormalizeProductName`, `TestNormalizeGenericName`, `TestNumericParsing`, `TestDateKey` | 30+ | NFKC, null tokens, zero-width chars, EAN-13 check digits, unit splitting, noise removal, numeric parsing, date keys |
| `synthetic_data_generator.py` | `TestGeneratorDeterminism`, `TestMasterDataStructure`, `TestTransactionDataStructure` | 8 | Byte-identical output, row counts, valid barcodes, scenario type coverage, line ID format |
| `data_quality.py` | `TestDuplicateDetection`, `TestNumericValidity`, `TestWellFormedIds`, `TestMasterReference`, `TestRunDataQuality` | 7 | Duplicate key detection, invalid numeric detection, malformed ID detection, orphan product detection, pipeline DQ integration |
| `matching.py` | `TestMatchingHierarchy` | 6 | Expected columns, primary ID matches found, unmatched lines exist, confidence ordering, one-result-per-A-line |
| `test_reconciliation.py` | `TestReconciliationStatuses`, `TestExposure`, `TestAnomalies`, `TestKPIs`, `TestReviewQueue` | 8 | Component statuses, review_required values, high confidence for matches, exposure non-negativity, anomaly severities, KPI valid ranges, branch/month KPIs, priority ordering |
| `pipeline.py` | `TestPipelineIntegration`, `TestGroundTruthRegression` | 11 | Pipeline completion, KPI computation, output file creation, all output files non-empty, dashboard JSON validity, scenario type coverage, clean match resolution, missing source detection, exception status presence |

---

## Key Test Scenarios

### Configuration Tests

| Test | What It Verifies |
|---|---|
| `test_random_seed_is_deterministic` | `RANDOM_SEED == 20260902` — fixed seed for reproducibility |
| `test_match_hierarchy_complete` | All 8 match methods present in hierarchy tuple |
| `test_match_hierarchy_order` | EXACT_PRIMARY_ID is first, UNMATCHED is last |
| `test_confidence_scores_ordered` | Confidence values strictly decreasing: 100 > 97 > 95 > 90 > 85 > 70 > 0 |
| `test_fuzzy_thresholds` | `0 < FUZZY_REVIEW_THRESHOLD < FUZZY_ACCEPT_THRESHOLD ≤ 1.0` |
| `test_reconciliation_statuses_defined` | Exactly 17 statuses defined |
| `test_exception_statuses_subset` | EXCEPTION_STATUSES is a proper subset of RECONCILIATION_STATUSES |
| `test_scenario_types_match_counts_keys` | SCENARIO_TYPES keys exactly match SCENARIO_COUNTS keys |

### Utility Tests

| Test | What It Verifies |
|---|---|
| `test_write_read_roundtrip` | CSV write → read produces identical data |
| `test_deterministic_hash` | Same dataframe written twice produces same SHA-256 |
| `test_frame_fingerprint_stable` | Same dataframe produces same fingerprint |
| `test_frame_fingerprint_detects_change` | Different data produces different fingerprint |
| `test_sorted_keys` | JSON output has alphabetically sorted keys |

### Normalization Tests

| Test | What It Verifies |
|---|---|
| `test_nfc_decomposition` | `"café"` → `"cafe"` (NFKC + combining mark removal) |
| `test_null_tokens` | `"n/a"`, `"null"`, `"-"`, `"?"` all normalize to empty string |
| `test_zero_width_removed` | Zero-width characters stripped from whitespace |
| `test_unit_split_equivalence` | `"ZENITH Cleaner 750ML"` == `"ZENITH Cleaner 750 ML"` after normalization |
| `test_noise_tokens_removed` | PACK, BOX, UNIT tokens removed from product names |
| `test_valid_ean13` | Generated barcodes pass EAN-13 check digit validation |
| `test_negative_parentheses` | `"(100.50)"` parses to `-100.50` |
| `test_currency_symbol` | `"$25.99"` parses to `25.99` |
| `test_comma_thousands` | `"1,234.56"` parses to `1234.56` |
| `test_invalid_text` | `"N/A"`, `"ERR"` parse to `None` |

### Synthetic Data Tests

| Test | What It Verifies |
|---|---|
| `test_deterministic_csvs` | Two consecutive `generate_all()` calls produce byte-identical CSV files |
| `test_product_master_count` | Exactly 150 products generated |
| `test_branch_master_count` | Exactly 10 branches generated |
| `test_employee_master_count` | Exactly 32 employees generated |
| `test_products_have_valid_barcodes` | All barcodes pass `is_valid_ean13()` |
| `test_expected_scenarios_covers_all_types` | All 28 scenario types present in ground truth |

### Data Quality Tests

| Test | What It Verifies |
|---|---|
| `test_detects_duplicate_keys` | Duplicate values in key columns produce `DUPLICATE_KEY` issues |
| `test_no_duplicates` | Unique keys produce zero issues |
| `test_detects_invalid_numeric` | Non-numeric values in quantity/price/amount columns produce `INVALID_NUMERIC` issues |
| `test_malformed_detected` | Non-alphanumeric identifiers produce `MALFORMED_IDENTIFIER` issues |
| `test_orphan_detected` | Product IDs not in master catalog produce `MISSING_MASTER_RECORD` issues |

### Matching Tests

| Test | What It Verifies |
|---|---|
| `test_match_results_has_expected_columns` | Result DataFrame contains `source_a_line_id`, `match_method`, `confidence_score` |
| `test_primary_id_matches_found` | `EXACT_PRIMARY_ID` appears in match results |
| `test_unmatched_lines_exist` | `UNMATCHED` appears in match results (injected scenarios ensure this) |
| `test_confidence_primary_id_is_highest` | All EXACT_PRIMARY_ID matches have confidence = 100 |
| `test_unmatched_confidence_is_zero` | All UNMATCHED lines have confidence = 0 |
| `test_each_a_line_produces_one_result` | Result count equals Source A line count |

### Reconciliation, Exposure, Anomaly, KPI, Review Queue Tests

| Test | What It Verifies |
|---|---|
| `test_recon_has_component_statuses` | `identity_status`, `quantity_status`, `price_status`, `amount_status` columns present |
| `test_review_required_is_y_or_n` | All values are `Y` or `N` |
| `test_matched_lines_have_high_confidence` | Mean confidence of MATCHED lines > 80 |
| `test_exposure_columns_present` | `signed_exposure`, `absolute_exposure` columns present |
| `test_absolute_exposure_non_negative` | All absolute exposure values ≥ 0 |
| `test_anomalies_have_severity` | Anomaly severities ∈ {LOW, MEDIUM, HIGH, CRITICAL} |
| `test_kpis_in_valid_range` | `0 ≤ match_rate_pct ≤ 100`, `0 ≤ exception_rate_pct ≤ 100`, `total_lines > 0` |
| `test_kpi_by_branch_written` | Branch KPI file has data with `branch_id` column |
| `test_kpi_by_month_written` | Month KPI file has data with `month_key` column |
| `test_review_has_priority` | Review priorities ∈ {CRITICAL, HIGH, MEDIUM, LOW} |
| `test_review_sorted_by_priority` | Priority values are non-decreasing in the queue |

### Pipeline Integration Tests

| Test | What It Verifies |
|---|---|
| `test_pipeline_completes` | `run_pipeline()` returns a non-None result |
| `test_kpis_computed` | KPIs have `total_lines > 0` and valid `match_rate_pct` |
| `test_output_files_created` | All output file paths exist on disk |
| `test_reconciliation_results_not_empty` | Reconciliation CSV has > 0 rows |
| `test_dashboard_data_json_valid` | JSON file is valid and contains `summary_kpis` and `status_distribution` |

### Ground Truth Regression Tests

| Test | What It Verifies |
|---|---|
| `test_all_scenario_types_present_in_ground_truth` | All 28 scenario types found in expected_scenarios.csv |
| `test_clean_exact_matches_are_matched` | ≥ 80% of CLEAN_EXACT_MATCH scenarios resolve to MATCHED status |
| `test_missing_in_source_detected` | At least one unmatched status exists in reconciliation results |
| `test_exception_statuses_present` | Pipeline produces at least one exception status beyond MATCHED |

---

## Running the Test Suite

```bash
# Run all tests with verbose output
pytest tests/ -v

# Run a specific test module
pytest tests/test_normalization.py -v

# Run a specific test class
pytest tests/test_config.py::TestConstants -v

# Run a specific test method
pytest tests/test_config.py::TestConstants::test_random_seed_is_deterministic -v

# Run with coverage (if pytest-cov installed)
pytest tests/ --cov=src --cov-report=term-missing
```

---

## Test Design Principles

1. **Determinism** — Tests rely on the fixed random seed; no test produces flaky results
2. **Ground truth validation** — The synthetic data generator creates a manifest of expected outcomes; pipeline tests verify alignment
3. **Boundary testing** — Tolerance thresholds (0.01, 0.02, 0.0001) are tested at boundary values
4. **Isolation** — Each test module focuses on a single pipeline module; integration tests are in `test_pipeline.py`
5. **No external dependencies** — Tests use `tmp_path` fixtures; no database or network connections required
