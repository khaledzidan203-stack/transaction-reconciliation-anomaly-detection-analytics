# KPI Dictionary

## Overview

The KPI framework (`src/kpis.py`) computes reconciliation performance metrics at three levels: summary (overall), by branch, and by month. Each level produces the same set of 10 KPIs, enabling consistent comparison across dimensions.

---

## Summary KPIs

Computed by `compute_kpis(recon_results)`.

### total_lines

| Attribute | Value |
|---|---|
| **Definition** | Total number of reconciliation line pairs |
| **Formula** | `COUNT(*)` of reconciliation results |
| **Data Type** | integer |
| **Valid Range** | ≥ 0 |
| **Unit** | Count |

---

### matched_lines

| Attribute | Value |
|---|---|
| **Definition** | Number of lines with clean match status |
| **Formula** | `COUNT WHERE reconciliation_status ∈ {MATCHED, MATCHED_WITH_SUBSTITUTE}` |
| **Data Type** | integer |
| **Valid Range** | 0 to `total_lines` |
| **Unit** | Count |
| **Interpretation** | Higher is better. Includes substitute matches because they represent a successful product identification, even if the brand differs. |

---

### exception_lines

| Attribute | Value |
|---|---|
| **Definition** | Number of lines with exception statuses |
| **Formula** | `COUNT WHERE reconciliation_status ∈ EXCEPTION_STATUSES` |
| **Data Type** | integer |
| **Valid Range** | 0 to `total_lines` |
| **Unit** | Count |
| **Exception statuses** | MISSING_IN_SOURCE_A, MISSING_IN_SOURCE_B, ADDITIONAL_TRANSACTION, ADDITIONAL_ITEM, QUANTITY_DIFFERENCE, PRICE_DIFFERENCE, AMOUNT_DIFFERENCE, QUANTITY_AND_AMOUNT_DIFFERENCE, FUZZY_MATCH_REVIEW, MASTER_DATA_EXCEPTION, DUPLICATE_KEY, DATA_QUALITY_EXCEPTION, UNRESOLVED |
| **Interpretation** | Lower is better. High exception rates may indicate source system data quality issues or matching engine calibration needs. |

---

### match_rate_pct

| Attribute | Value |
|---|---|
| **Definition** | Percentage of lines that matched |
| **Formula** | `(matched_lines / total_lines) × 100` |
| **Data Type** | float |
| **Valid Range** | 0.00 to 100.00 |
| **Unit** | Percentage |
| **Precision** | 2 decimal places |
| **Interpretation** | Target: typically > 90% for well-calibrated systems. Below 80% warrants investigation into source data quality and matching thresholds. |

---

### exception_rate_pct

| Attribute | Value |
|---|---|
| **Definition** | Percentage of lines with exceptions |
| **Formula** | `(exception_lines / total_lines) × 100` |
| **Data Type** | float |
| **Valid Range** | 0.00 to 100.00 |
| **Unit** | Percentage |
| **Precision** | 2 decimal places |
| **Interpretation** | Complementary to match_rate_pct. `match_rate_pct + exception_rate_pct` may not equal 100 because MATCHED_WITH_SUBSTITUTE is counted in matched_lines but also flagged for review. |

---

### total_absolute_exposure

| Attribute | Value |
|---|---|
| **Definition** | Sum of absolute exposure across all lines |
| **Formula** | `SUM(absolute_exposure)` |
| **Data Type** | float |
| **Valid Range** | ≥ 0.00 |
| **Unit** | Currency |
| **Precision** | 2 decimal places |
| **Interpretation** | Represents the total gross discrepancy between source systems. This is the broadest measure of financial impact. |

---

### unresolved_exposure

| Attribute | Value |
|---|---|
| **Definition** | Exposure from lines that could not be reconciled |
| **Formula** | `SUM(unresolved_exposure)` where `unresolved_exposure > 0` |
| **Data Type** | float |
| **Valid Range** | ≥ 0.00 |
| **Unit** | Currency |
| **Precision** | 2 decimal places |
| **Interpretation** | The most critical exposure metric. These are amounts with no identified counterpart — the full amount is potentially discrepant. |

---

### average_confidence

| Attribute | Value |
|---|---|
| **Definition** | Mean confidence score across all matched lines |
| **Formula** | `AVG(confidence_score)` |
| **Data Type** | float |
| **Valid Range** | 0.00 to 100.00 |
| **Unit** | Score |
| **Precision** | 2 decimal places |
| **Interpretation** | Higher is better. Below 80 suggests many fuzzy/low-confidence matches. Track trends — declining average confidence may indicate source data degradation. |

---

### review_required_count

| Attribute | Value |
|---|---|
| **Definition** | Number of lines flagged for manual review |
| **Formula** | `COUNT WHERE review_required = 'Y'` |
| **Data Type** | integer |
| **Valid Range** | 0 to `total_lines` |
| **Unit** | Count |
| **Interpretation** | Represents the manual workload for analysts. Track this over time to assess whether matching improvements are reducing the review burden. |

---

### review_rate_pct

| Attribute | Value |
|---|---|
| **Definition** | Percentage of lines requiring manual review |
| **Formula** | `(review_required_count / total_lines) × 100` |
| **Data Type** | float |
| **Valid Range** | 0.00 to 100.00 |
| **Unit** | Percentage |
| **Precision** | 2 decimal places |
| **Interpretation** | Complementary to match_rate_pct. High review rates indicate either conservative matching thresholds or significant data quality issues. |

---

## KPIs by Branch

Computed by `compute_kpis_by_branch(recon, a_headers, b_headers)`.

Produces the same 10 KPIs per branch. Branch is resolved by:
1. Mapping `source_a_transaction_id` → `branch_id` from Source A headers
2. If missing, falling back to `source_b_transaction_id` → `branch_id` from Source B headers
3. If both missing, branch = `"UNKNOWN"`

**Output columns:** All 10 summary KPI columns + `branch_id`

---

## KPIs by Month

Computed by `compute_kpis_by_month(recon, a_headers, b_headers)`.

Produces the same 10 KPIs per calendar month. Month is resolved by:
1. Mapping `source_a_transaction_id` → `transaction_date` from Source A headers
2. If missing, falling back to `source_b_transaction_id` → `transaction_date` from Source B headers
3. Extracting ISO `YYYY-MM` month key via `date_key()`
4. If date is missing or unparseable, `month_key` = `"UNKNOWN"`

**Output columns:** All 10 summary KPI columns + `month_key`

**Months in synthetic data:** `2026-01`, `2026-02`, `2026-03`, `2026-04`

---

## KPI Relationships

```
total_lines = matched_lines + exception_lines + (other non-exception, non-match lines)

match_rate_pct  = matched_lines / total_lines × 100
exception_rate_pct = exception_lines / total_lines × 100
review_rate_pct = review_required_count / total_lines × 100

total_absolute_exposure ≥ unresolved_exposure
total_absolute_exposure ≥ review_exposure (from exposure module)
unresolved_exposure ≤ total_absolute_exposure
```

**Note:** `matched_lines + exception_lines` may not equal `total_lines` because `MATCHED_WITH_SUBSTITUTE` is counted as matched but is also flagged for review (and thus appears in `review_required_count`).

---

## KPI Use Cases

| Use Case | KPIs to Monitor |
|---|---|
| Overall reconciliation health | `match_rate_pct`, `exception_rate_pct` |
| Financial risk assessment | `total_absolute_exposure`, `unresolved_exposure` |
| Analyst workload planning | `review_required_count`, `review_rate_pct` |
| Matching engine calibration | `average_confidence`, `match_rate_pct` by match method |
| Branch performance comparison | All KPIs by branch |
| Trend analysis | All KPIs by month |
| Data quality monitoring | `exception_rate_pct` broken down by exception type |
