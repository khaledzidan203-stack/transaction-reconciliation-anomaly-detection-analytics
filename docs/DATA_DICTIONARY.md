# Data Dictionary

Complete specification of every table and column in the reconciliation analytics pipeline.

---

## Table Overview

| Table | Source | Grain | Row Count (approx.) |
|---|---|---|---|
| `product_master` | Generated | One row per product | 150 |
| `branch_master` | Generated | One row per branch | 10 |
| `employee_master` | Generated | One row per employee | 32 |
| `source_a_transaction_headers` | Generated | One row per Source A transaction | ~2,200+ |
| `source_a_transaction_lines` | Generated | One row per Source A line item | ~2,200+ |
| `source_b_transaction_headers` | Generated | One row per Source B transaction | ~2,200+ |
| `source_b_transaction_lines` | Generated | One row per Source B line item | ~2,200+ |
| `expected_scenarios` | Generated | One row per injected scenario | ~2,300+ |
| `reconciliation_results` | Pipeline output | One row per reconciled line pair | ~2,300+ |
| `data_quality_issues` | Pipeline output | One row per DQ issue | Variable |
| `anomaly_results` | Pipeline output | One row per anomaly | Variable |
| `review_queue` | Pipeline output | One row per review-required line | Variable |
| `kpi_summary` | Pipeline output | One row (summary KPIs) | 1 |
| `kpi_by_branch` | Pipeline output | One row per branch | 10 |
| `kpi_by_month` | Pipeline output | One row per month | 4 |

---

## 1. product_master.csv

Reference catalog of 150 fictional products across 8 categories.

| Column | Data Type | Description | Example |
|---|---|---|---|
| `product_id` | string | Unique product identifier | `PRD-0001` |
| `product_code` | string | Alternate product code | `PC-ZEN0001` |
| `barcode` | string | EAN-13 barcode (13 digits, valid check digit) | `2000000000015` |
| `product_name` | string | Full commercial product name (brand + base + strength) | `ZENITH All Purpose Cleaner 250 ML` |
| `generic_name` | string | Generic product type name (brand-independent) | `All Purpose Cleaner 250 ML` |
| `brand` | string | Brand prefix | `ZENITH` |
| `category` | string | Product category | `Household` |
| `strength` | string | Strength or specification | `250 ML` |
| `reference_unit_price` | string | Canonical unit price (string, 2 decimals) | `45.67` |

**Categories:** Household, Office Supplies, Electronics Accessories, Personal Care, Kitchen, Stationery, Hardware, Beverages

**Brands:** ZENITH, AURORA, NEXUS (3 brands per base product)

---

## 2. branch_master.csv

Reference catalog of 10 fictional branches.

| Column | Data Type | Description | Example |
|---|---|---|---|
| `branch_id` | string | Unique branch identifier | `BR-001` |
| `branch_name` | string | Branch display name | `Northport Branch` |
| `city` | string | City name | `Northport` |
| `region` | string | Region (first word of city) | `Northport` |

**Cities:** Northport, Eastvale, Southfield, Westbrook, Cedar Hills, Maple Ridge, Pine Valley, Oakwood, Riverside, Lakeside

---

## 3. employee_master.csv

Reference catalog of 32 fictional employees.

| Column | Data Type | Description | Example |
|---|---|---|---|
| `employee_id` | string | Unique employee identifier | `EMP-0001` |
| `employee_label` | string | Neutral display name | `Employee 0001` |
| `branch_id` | string | Assigned branch (cyclic distribution) | `BR-001` |

Employee-to-branch assignment: `branch_id = BR-{((idx-1) % 10) + 1:03d}`

---

## 4. source_a_transaction_headers.csv

Transaction header records from Source A (POS System).

| Column | Data Type | Description | Example |
|---|---|---|---|
| `transaction_id` | string | Unique transaction identifier | `TXN-A-000123` |
| `branch_id` | string | Branch where transaction occurred | `BR-003` |
| `employee_id` | string | Employee who processed the transaction | `EMP-0015` |
| `transaction_date` | string | ISO date (YYYY-MM-DD) | `2026-02-17` |
| `transaction_type` | string | Transaction type: `SALE`, `CREDIT`, `REVERSAL` | `SALE` |
| `total_amount` | string | Total transaction amount (string, 2 decimals) | `234.56` |
| `source` | string | Source system label | `SOURCE_A` |

---

## 5. source_a_transaction_lines.csv

Transaction line items from Source A (POS System).

| Column | Data Type | Description | Example |
|---|---|---|---|
| `line_id` | string | Unique line identifier | `TXN-A-000123-L01` |
| `transaction_id` | string | Parent transaction identifier | `TXN-A-000123` |
| `product_id` | string | Product master identifier | `PRD-0042` |
| `product_code` | string | Product code | `PC-ZEN0042` |
| `barcode` | string | EAN-13 barcode | `2000000004213` |
| `product_name` | string | Product commercial name | `ZENITH Glass Spray 500 ML` |
| `generic_name` | string | Generic product type | `Glass Spray 500 ML` |
| `quantity` | string | Quantity (string representation) | `5.0` |
| `unit_price` | string | Unit price (string representation) | `12.99` |
| `amount` | string | Line amount (string representation) | `64.95` |
| `reference_id` | string | Cross-reference to Source B transaction ID | `TXN-B-000456` |
| `source` | string | Source system label | `SOURCE_A` |

**Normalized columns added at ingestion** (not in CSV, added by `ingestion.py`):

| Column | Data Type | Description |
|---|---|---|
| `_source` | string | Source label (`SOURCE_A` or `SOURCE_B`) |
| `_norm_product_name` | string | Normalized product name key (uppercase, noise removed, unit-split) |
| `_norm_barcode` | string | Digits-only normalized barcode |
| `_norm_product_code` | string | Separator-stripped normalized product code |
| `_norm_reference_id` | string | Normalized cross-reference identifier |
| `_norm_txn_id` | string | Normalized transaction identifier |
| `_qty_float` | float | Parsed quantity value (NaN if unparseable) |
| `_price_float` | float | Parsed unit price value (NaN if unparseable) |
| `_amount_float` | float | Parsed amount value (NaN if unparseable) |

---

## 6. source_b_transaction_headers.csv

Identical structure to Source A headers. Columns: `transaction_id`, `branch_id`, `employee_id`, `transaction_date`, `transaction_type`, `total_amount`, `source` (value: `SOURCE_B`).

---

## 7. source_b_transaction_lines.csv

Identical structure to Source A lines. Same columns and normalized additions. `source` = `SOURCE_B`.

---

## 8. expected_scenarios.csv

Ground-truth manifest of injected scenarios for regression testing.

| Column | Data Type | Description | Example |
|---|---|---|---|
| `scenario_id` | string | Unique scenario identifier | `SCN-0001` |
| `scenario_type` | string | One of 28 scenario type names | `CLEAN_EXACT_MATCH` |
| `source_a_transaction_id` | string | Source A transaction (empty if N/A) | `TXN-A-000001` |
| `source_b_transaction_id` | string | Source B transaction (empty if N/A) | `TXN-B-000001` |
| `source_a_line_id` | string | Source A line (empty if N/A) | `TXN-A-000001-L01` |
| `source_b_line_id` | string | Source B line (empty if N/A) | `TXN-B-000001-L01` |
| `expected_match_method` | string | Expected matching method | `EXACT_PRIMARY_ID` |
| `expected_reconciliation_status` | string | Expected reconciliation status | `MATCHED` |
| `expected_review_required` | string | Expected review flag | `N` or `Y` |
| `expected_notes` | string | Human-readable scenario description | `Exact match on all fields` |

---

## 9. reconciliation_results.csv

Primary pipeline output: one row per reconciled line pair.

| Column | Data Type | Description |
|---|---|---|
| `source_a_line_id` | string | Source A line identifier (empty if only in B) |
| `source_a_transaction_id` | string | Source A transaction identifier |
| `source_b_line_id` | string | Source B line identifier (empty if only in A) |
| `source_b_transaction_id` | string | Source B transaction identifier |
| `match_method` | string | Matching method used (one of 8 levels) |
| `confidence_score` | float | Match confidence (0–100) |
| `identity_status` | string | Identity component: `IDENTITY_MATCHED`, `IDENTITY_SUBSTITUTE`, `IDENTITY_UNMATCHED`, `IDENTITY_MISSING_IN_SOURCE_A`, `IDENTITY_MISSING_IN_SOURCE_B` |
| `quantity_status` | string | Quantity component: `QUANTITY_MATCHED`, `QUANTITY_SHORTAGE`, `QUANTITY_EXCESS`, `QUANTITY_NOT_APPLICABLE` |
| `price_status` | string | Price component: `PRICE_MATCHED`, `PRICE_VARIANCE`, `PRICE_NOT_APPLICABLE` |
| `amount_status` | string | Amount component: `AMOUNT_MATCHED`, `AMOUNT_VARIANCE`, `AMOUNT_NOT_APPLICABLE` |
| `reconciliation_status` | string | Overall status (one of 17 statuses) |
| `review_required` | string | `Y` or `N` |
| `quantity_difference` | float | `source_a_qty − source_b_qty` (None if not applicable) |
| `price_difference` | float | `source_a_price − source_b_price` (None if not applicable) |
| `amount_difference` | float | `source_a_amount − source_b_amount` (None if not applicable) |
| `source_a_product_id` | string | Product ID from Source A |
| `source_b_product_id` | string | Product ID from Source B |
| `source_a_product_name` | string | Product name from Source A |
| `source_b_product_name` | string | Product name from Source B |
| `source_a_amount` | float | Amount from Source A (0.0 if missing) |
| `source_b_amount` | float | Amount from Source B (0.0 if missing) |
| `source_a_quantity` | float | Quantity from Source A (None if missing) |
| `source_b_quantity` | float | Quantity from Source B (None if missing) |
| `source_a_unit_price` | float | Unit price from Source A (None if missing) |
| `source_b_unit_price` | float | Unit price from Source B (None if missing) |
| `signed_exposure` | float | `source_a_amount − source_b_amount` |
| `absolute_exposure` | float | `|signed_exposure|` |
| `quantity_exposure` | float | `|quantity_difference × source_b_unit_price|` |
| `price_exposure` | float | `|price_difference × source_a_quantity|` |
| `amount_exposure` | float | Residual: `max(absolute − quantity − price, 0)` |
| `unresolved_exposure` | float | Full amount for UNRESOLVED/MISSING statuses |
| `review_exposure` | float | `absolute_exposure` where `review_required = 'Y'` |

---

## 10. data_quality_issues.csv

One row per detected data quality issue.

| Column | Data Type | Description | Example |
|---|---|---|---|
| `table` | string | Table where the issue was found | `source_a_lines` |
| `field` | string | Column where the issue was found | `product_id` |
| `issue_type` | string | Issue category | `MALFORMED_IDENTIFIER` |
| `severity` | string | `ERROR`, `WARNING`, or `BUSINESS_ANOMALY` | `ERROR` |
| `description` | string | Human-readable issue description | `Identifier 'PRD!01#' is not well formed` |
| `record_key` | string | Key of the affected record | `PRD!01#` |

**Issue types:**

| Issue Type | Severity | Description |
|---|---|---|
| `MISSING_COLUMN` | ERROR | Required column absent from table |
| `UNEXPECTED_COLUMN` | WARNING | Unexpected column found in table |
| `DUPLICATE_KEY` | ERROR | Duplicate value in a key column |
| `MALFORMED_IDENTIFIER` | ERROR | Identifier fails alphanumeric validation |
| `INVALID_NUMERIC` | ERROR | Numeric value cannot be parsed |
| `MISSING_VALUE` | ERROR | Required field is null or empty |
| `MISSING_MASTER_RECORD` | BUSINESS_ANOMALY | Transaction references non-existent master record |

---

## 11. anomaly_results.csv

One row per detected anomaly.

| Column | Data Type | Description | Example |
|---|---|---|---|
| `line_key` | string | Source line identifier | `TXN-A-000123-L01` |
| `anomaly_type` | string | Anomaly rule that triggered | `HIGH_VALUE_OUTLIER` |
| `severity` | string | `LOW`, `MEDIUM`, `HIGH`, or `CRITICAL` | `HIGH` |
| `description` | string | Human-readable anomaly description | `Amount 523.40 exceeds 5.0x population mean 45.67` |
| `reconciliation_status` | string | Reconciliation status of the line | `MATCHED` |

---

## 12. review_queue.csv

Prioritized queue of items requiring manual review.

| Column | Data Type | Description | Example |
|---|---|---|---|
| `line_key` | string | Source line identifier | `TXN-A-000123-L01` |
| `priority` | string | `CRITICAL`, `HIGH`, `MEDIUM`, or `LOW` | `CRITICAL` |
| `reconciliation_status` | string | Reconciliation status | `DATA_QUALITY_EXCEPTION` |
| `match_method` | string | Matching method used | `UNMATCHED` |
| `confidence_score` | float | Match confidence | `0.0` |
| `absolute_exposure` | float | Absolute financial exposure | `234.56` |
| `anomaly_flags` | string | Semicolon-separated anomaly types | `DATA_QUALITY_FAILURE;HIGH_VALUE_OUTLIER` |

---

## 13. kpi_summary.csv

Single-row summary of top-level KPIs.

| Column | Data Type | Description |
|---|---|---|
| `total_lines` | int | Total reconciliation line pairs |
| `matched_lines` | int | Lines with MATCHED or MATCHED_WITH_SUBSTITUTE |
| `exception_lines` | int | Lines with exception statuses |
| `match_rate_pct` | float | `(matched_lines / total_lines) × 100` |
| `exception_rate_pct` | float | `(exception_lines / total_lines) × 100` |
| `total_absolute_exposure` | float | Sum of absolute exposure |
| `unresolved_exposure` | float | Exposure from UNRESOLVED / MISSING cases |
| `average_confidence` | float | Mean match confidence score |
| `review_required_count` | int | Lines flagged for manual review |
| `review_rate_pct` | float | `(review_required_count / total_lines) × 100` |

---

## 14. kpi_by_branch.csv

Per-branch KPIs. Same columns as `kpi_summary.csv` plus:

| Column | Data Type | Description |
|---|---|---|
| `branch_id` | string | Branch identifier |

Branch is resolved by joining `source_a_transaction_id` to headers; falls back to Source B header if Source A is missing.

---

## 15. kpi_by_month.csv

Per-month KPIs. Same columns as `kpi_summary.csv` plus:

| Column | Data Type | Description |
|---|---|---|
| `month_key` | string | ISO month key (`YYYY-MM`) |

Month is extracted from transaction dates via `date_key()`.

---

## 16. dashboard_data.json

Consolidated JSON payload for dashboard consumption.

| Key | Type | Description |
|---|---|---|
| `summary_kpis` | object | Same as kpi_summary.csv |
| `kpi_by_branch` | array | Same as kpi_by_branch.csv |
| `kpi_by_month` | array | Same as kpi_by_month.csv |
| `status_distribution` | object | `{status: count}` distribution |
| `match_method_distribution` | object | `{method: count}` distribution |
| `anomaly_summary` | object | `{anomaly_type: count}` distribution |
| `review_priority_distribution` | object | `{priority: count}` distribution |

---

## 17. generation_manifest.json

Metadata about the synthetic data generation run.

| Key | Type | Description |
|---|---|---|
| `seed` | int | Random seed used (`20260902`) |
| `files` | object | Map of filename → `{rows, columns, column_names, sha256}` |
| `scenario_counts` | object | Map of scenario type → count generated |
| `generated_at` | string | ISO timestamp of generation |
