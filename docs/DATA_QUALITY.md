# Data Quality Framework

## Overview

The data quality engine (`src/data_quality.py` and `src/schema_validation.py`) runs a battery of deterministic checks against source data before and during reconciliation. Issues are classified by severity and tracked alongside reconciliation results so that data quality problems are visible throughout the pipeline.

---

## Check Types

### Schema Validation (`schema_validation.py`)

Validates that each input table has the expected column structure. Seven tables are checked:

| Table | Expected Column Count |
|---|---|
| `product_master` | 9 columns |
| `branch_master` | 4 columns |
| `employee_master` | 3 columns |
| `source_a_headers` | 7 columns |
| `source_a_lines` | 12 columns |
| `source_b_headers` | 7 columns |
| `source_b_lines` | 12 columns |

**Check 1: MISSING_COLUMN**
- **Trigger:** A required column is absent from the table
- **Severity:** `ERROR`
- **Description:** `"Required column '{col}' is missing from {table_name}"`
- **Impact:** Downstream normalization and matching will fail for missing columns

**Check 2: UNEXPECTED_COLUMN**
- **Trigger:** A column exists in the table that is not in the expected schema (excluding internal `_` prefixed columns)
- **Severity:** `WARNING`
- **Description:** `"Unexpected column '{col}' in {table_name}"`
- **Impact:** No functional impact; may indicate schema drift or version mismatch

**Note:** Columns added by the ingestion layer (prefixed with `_`) are excluded from unexpected column checks. These include `_source`, `_norm_product_name`, `_norm_barcode`, etc.

---

### Duplicate Key Detection (`data_quality.py`)

**Check: DUPLICATE_KEY**
- **Trigger:** A value appears more than once in a key column
- **Severity:** `ERROR`
- **Columns checked:**
  - `source_a_headers.transaction_id`
  - `source_b_headers.transaction_id`
  - `source_a_lines.line_id`
  - `source_b_lines.line_id`
- **Method:** `pandas.DataFrame.duplicated(keep=False)` — marks all occurrences of a duplicate value
- **Description:** `"Duplicate {key_col} value: {val}"`

**Design:** `keep=False` means *all* rows sharing a duplicate value are flagged, not just the second occurrence. This ensures no duplicate is overlooked.

---

### Malformed Identifier Detection

**Check: MALFORMED_IDENTIFIER**
- **Trigger:** An identifier value is non-empty and fails the `is_well_formed_identifier()` test
- **Severity:** `ERROR`
- **Columns checked:**
  - `source_a_lines.product_id`
  - `source_b_lines.product_id`
- **Well-formedness rule:** After `normalize_identifier()` (strip separators, uppercase), the value must be non-empty and alphanumeric
- **Description:** `"Identifier '{val}' is not well formed"`

**Example of malformed identifiers:**
- `PRD!01#` — contains non-alphanumeric characters `!` and `#`
- `PRD- 001` — after stripping separators, internal whitespace creates a non-alphanumeric value

**Example of well-formed identifiers:**
- `PRD0001` → normalized: `PRD0001` ✅
- `PRD-0001` → normalized: `PRD0001` ✅
- `TXN-A-000123` → normalized: `TXNA000123` ✅

---

### Invalid Numeric Detection

**Check: INVALID_NUMERIC**
- **Trigger:** A text value in a numeric column cannot be parsed by `parse_number()`, and the corresponding float column is NaN
- **Severity:** `ERROR`
- **Columns checked (per source):**
  - `quantity` vs `_qty_float`
  - `unit_price` vs `_price_float`
  - `amount` vs `_amount_float`
- **Description:** `"Non-numeric value '{val}' in {col}"`

**Method:** The check compares the original text column against the parsed float column. If the text is non-empty but the float is NaN, the value is invalid.

**Invalid numeric examples:**
- `"N/A"`, `"ERR"`, `"TBD"`, `"abc"` → parse to None → float = NaN
- `""` → treated as missing, not invalid (no issue raised)
- `None` → treated as missing, not invalid

**Valid numeric examples:**
- `"42.5"` → parses to 42.5 ✅
- `"1,234.56"` → parses to 1234.56 ✅
- `"(100.50)"` → parses to -100.50 ✅
- `"$25.99"` → parses to 25.99 ✅

---

### Missing Value Detection

**Check: MISSING_VALUE**
- **Trigger:** A required field is null or empty
- **Severity:** `ERROR`
- **Description:** `"Missing required value in {col}"`

**Note:** This check is defined in `data_quality.py` but is not actively called in the current pipeline. It is available for deployment-specific customization.

---

### Missing Master Record Detection

**Check: MISSING_MASTER_RECORD**
- **Trigger:** A transaction line references a `product_id` that does not exist in the product master table (after normalization)
- **Severity:** `BUSINESS_ANOMALY`
- **Columns checked:**
  - `source_a_lines.product_id` against `product_master.product_id`
  - `source_b_lines.product_id` against `product_master.product_id`
- **Description:** `"Product '{raw_id}' not found in master data"`
- **Method:** Normalized product IDs from source lines are compared against the set of normalized master product IDs

**Why BUSINESS_ANOMALY instead of ERROR:** An orphan product ID may represent a legitimate new product not yet cataloged, rather than a data error. The BUSINESS_ANOMALY severity signals that the situation is unusual but potentially valid.

---

## Severity Classes

| Severity | Numeric | Description | Pipeline Impact |
|---|---|---|---|
| `ERROR` | Highest | Critical issue that may prevent processing | Matching may fail or produce unreliable results for affected rows |
| `WARNING` | Medium | Notable issue; processing continues | Informational; no functional impact |
| `BUSINESS_ANOMALY` | Lowest | Unusual but potentially valid pattern | Flagged for analyst review; does not block processing |

---

## DQ Issue Schema

| Field | Data Type | Description | Example |
|---|---|---|---|
| `table` | string | Table where the issue was found | `source_a_lines` |
| `field` | string | Column where the issue was found | `product_id` |
| `issue_type` | string | Category of the issue | `MALFORMED_IDENTIFIER` |
| `severity` | string | `ERROR`, `WARNING`, or `BUSINESS_ANOMALY` | `ERROR` |
| `description` | string | Human-readable description | `Identifier 'PRD!01#' is not well formed` |
| `record_key` | string | Key of the affected record | `PRD!01#` |

---

## Integration with Pipeline

1. **Schema validation** runs at ingestion time, before any data quality checks
2. **Data quality checks** run after ingestion but before matching
3. **DQ issues** are written to `data_quality_issues.csv` and included in `dashboard_data.json`
4. **Reconciliation status** references DQ: lines with `DATA_QUALITY_EXCEPTION` status indicate a DQ issue prevented matching
5. **Anomaly detection** Rule 3 (`DATA_QUALITY_FAILURE`) flags DQ exceptions as CRITICAL anomalies
6. **Review queue** assigns CRITICAL priority to `DATA_QUALITY_EXCEPTION` lines

---

## DQ Check Execution Summary

| Check | Module | Tables | Columns | Issue Type | Severity |
|---|---|---|---|---|---|
| Schema: missing columns | `schema_validation` | 7 tables | All expected | `MISSING_COLUMN` | ERROR |
| Schema: unexpected columns | `schema_validation` | 7 tables | All | `UNEXPECTED_COLUMN` | WARNING |
| Duplicate keys | `data_quality` | 4 tables | 4 key columns | `DUPLICATE_KEY` | ERROR |
| Malformed identifiers | `data_quality` | 2 tables | `product_id` | `MALFORMED_IDENTIFIER` | ERROR |
| Invalid numerics | `data_quality` | 2 tables | `quantity`, `unit_price`, `amount` | `INVALID_NUMERIC` | ERROR |
| Missing master refs | `data_quality` | 2 tables | `product_id` | `MISSING_MASTER_RECORD` | BUSINESS_ANOMALY |

---

## Synthetic Data DQ Scenarios

The synthetic data generator deliberately injects the following DQ-triggering scenarios:

| Scenario | DQ Issue Type | Expected Count | Description |
|---|---|---|---|
| `DUPLICATE_TRANSACTION_KEY` | `DUPLICATE_KEY` | 20 | Same transaction_id appears twice in Source A headers |
| `DUPLICATE_LINE` | `DUPLICATE_KEY` | 25 | Same line_id appears twice in a Source A transaction |
| `MISSING_MASTER_RECORD` | `MISSING_MASTER_RECORD` | 30 | Product ID not in master catalog (e.g., `PRD-ORPH1234`) |
| `MALFORMED_IDENTIFIER` | `MALFORMED_IDENTIFIER` | 25 | Corrupted product_id format (e.g., `PRD!01#`) |
| `INVALID_NUMERIC` | `INVALID_NUMERIC` | 25 | Non-numeric quantity or price value (e.g., `"N/A"`, `"ERR"`) |

These controlled injections ensure that the DQ engine is exercised by every pipeline run and that tests can verify specific DQ issue counts.
