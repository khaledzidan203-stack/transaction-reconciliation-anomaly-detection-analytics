# Business Requirements

## Document Purpose

This document defines the business requirements for the Transaction Reconciliation & Anomaly Detection Analytics framework. It specifies what the system must accomplish, the data it must handle, and the constraints it must satisfy.

---

## 1. Problem Statement

Organizations that process transactions across multiple systems face recurring reconciliation challenges:

1. **Transaction misalignment** — Transactions recorded in one system may be missing, duplicated, or altered in another, leading to financial discrepancies that compound over time.

2. **Product identifier divergence** — Product identifiers, names, barcodes, and codes frequently differ across source systems due to independent data management, vendor changes, or system migrations.

3. **Quantitative variances** — Quantities, unit prices, and line amounts may diverge due to timing differences, rounding conventions, data-entry errors, or system-specific calculation logic.

4. **Manual review burden** — Exceptions accumulate in manual review queues, requiring analyst judgment and consuming disproportionate operational resources.

5. **Financial exposure opacity** — Without systematic quantification, the financial impact of unreconciled items remains invisible until it surfaces as audit findings or financial adjustments.

6. **Anomaly blindness** — Unusual patterns in transaction volumes, amounts, match rates, and exception concentrations may indicate data quality issues, operational risks, or process failures, but are difficult to detect without automated monitoring.

A robust reconciliation framework must address these challenges through deterministic matching, constrained fuzzy matching, data quality controls, anomaly detection, and transparent exposure calculation.

---

## 2. Objectives

| # | Objective | Success Metric |
|---|---|---|
| 1 | Match transactions across two source systems using a transparent, explainable hierarchy | Every match decision traceable to method, confidence, and evidence |
| 2 | Validate data quality before reconciliation | 100% of source data screened for schema, format, and reference integrity |
| 3 | Quantify financial exposure by category | Signed, absolute, and decomposed exposure for every line |
| 4 | Detect analytical anomalies | 7 rule-based detectors covering amount, confidence, DQ, and master data anomalies |
| 5 | Prioritize manual review | Priority-ordered queue (CRITICAL → LOW) based on status, exposure, and anomaly severity |
| 6 | Produce actionable KPIs | 10 metrics at summary, branch, and month levels |
| 7 | Ensure full reproducibility | Byte-identical outputs across runs with the same seed |
| 8 | Protect privacy | No real business data in the portfolio demonstration |

---

## 3. Scope

### In Scope

- Two-source transaction reconciliation (Source A / Source B)
- Deterministic synthetic data generation with 28 controlled scenarios
- 8-level hierarchical matching engine
- 4-component reconciliation status (identity, quantity, price, amount)
- 17 reconciliation statuses
- Financial exposure decomposition (7 exposure types)
- 7 anomaly detection rules with 4 severity levels
- Prioritized review queue (4 priority levels)
- KPI computation (summary, by branch, by month)
- CSV and JSON output generation
- Full automated test coverage
- Comprehensive documentation

### Out of Scope

- Real business data ingestion or processing
- Multi-source reconciliation (3+ systems)
- Machine learning-based matching or anomaly detection
- Real-time or streaming reconciliation
- User interface for data correction
- Integration with external ERP/accounting systems
- Regulatory compliance reporting
- Role-based access control

---

## 4. Data Requirements

### 4.1 Source Systems

| System | Label | Role |
|---|---|---|
| Source A | POS System | Primary transaction recording system |
| Source B | Reference System | Secondary/billing transaction system |

Both sources share the same data model (headers + lines) with identical column structures.

### 4.2 Data Entities

| Entity | Required Columns | Key |
|---|---|---|
| Product Master | product_id, product_code, barcode, product_name, generic_name, brand, category, strength, reference_unit_price | product_id |
| Branch Master | branch_id, branch_name, city, region | branch_id |
| Employee Master | employee_id, employee_label, branch_id | employee_id |
| Transaction Header | transaction_id, branch_id, employee_id, transaction_date, transaction_type, total_amount, source | transaction_id |
| Transaction Line | line_id, transaction_id, product_id, product_code, barcode, product_name, generic_name, quantity, unit_price, amount, reference_id, source | line_id |

### 4.3 Transaction Types

| Type | Description |
|---|---|
| `SALE` | Standard sale transaction |
| `CREDIT` | Credit/return transaction |
| `REVERSAL` | Reversal/cancellation transaction |

### 4.4 Data Quality Requirements

- All identifiers must be non-empty and well-formed (alphanumeric after normalization)
- Numeric fields (quantity, unit_price, amount) must be parseable
- Transaction and line keys must be unique within each source
- Product references must exist in the product master catalog
- Dates must be valid ISO format

### 4.5 Synthetic Data Requirements

- Fully reproducible via a fixed random seed (`20260902`)
- No real business data, names, or identifiers
- 28 controlled scenario types covering every matching level and exception type
- Ground-truth manifest for regression testing
- SHA-256 fingerprint verification of all output files

---

## 5. Matching Requirements

### 5.1 Hierarchy Requirements

The matching engine must implement a strict 8-level hierarchy:

| Priority | Method | Confidence |
|---|---|---|
| 1 | Exact Primary ID (reference_id + product_id) | 100 |
| 2 | Exact Barcode | 97 |
| 3 | Exact Product Code | 95 |
| 4 | Normalized Name | 90 |
| 5 | Fuzzy Name (accept ≥0.92, review 0.80–0.92) | score × 100 |
| 6 | Generic Strength Equivalent | 85 |
| 7 | Possible Substitute (fuzzy generic ≥0.70) | 70 |
| 8 | Unmatched | 0 |

### 5.2 Determinism Requirements

- The first matching level that succeeds determines the result; lower levels are not attempted
- Each Source B line may be matched to at most one Source A line (consumption rule)
- Fuzzy matching must use deterministic algorithms (token_sort_ratio, partial_ratio from rapidfuzz)
- Thresholds must be configurable via `config.py`

### 5.3 Performance Requirements

- Fuzzy matching must use inverted token indexing to avoid O(n²) full scans
- Token index tokens must be ≥ 3 characters to reduce noise

### 5.4 Explainability Requirements

- Every match result must record: match_method, confidence_score, fuzzy_score, fuzzy_threshold_band
- Fuzzy matches must indicate whether they are in the ACCEPT or REVIEW band

---

## 6. Reconciliation Requirements

### 6.1 Component Statuses

The system must independently compute four component statuses:

| Component | Statuses | Tolerance |
|---|---|---|
| Identity | MATCHED, SUBSTITUTE, UNMATCHED, MISSING_A, MISSING_B | N/A |
| Quantity | MATCHED, SHORTAGE, EXCESS, NOT_APPLICABLE | ±0.0001 |
| Price | MATCHED, VARIANCE, NOT_APPLICABLE | ±0.01 |
| Amount | MATCHED, VARIANCE, NOT_APPLICABLE | ±0.02 |

### 6.2 Overall Status Derivation

The overall status must be derived from component statuses using a priority-based decision tree:
1. Transaction type override (CREDIT, REVERSAL)
2. Unmatched side classification (MISSING_IN_SOURCE_A/B)
3. Low-confidence fuzzy review
4. Identity-based classification
5. Component variance override (quantity, price, amount)

17 distinct statuses must be supported.

### 6.3 Review Routing

All exception statuses and MATCHED_WITH_SUBSTITUTE must be flagged for manual review.

---

## 7. Exposure Requirements

### 7.1 Exposure Dimensions

| Dimension | Formula | Required |
|---|---|---|
| Signed Exposure | source_a_amount − source_b_amount | ✅ |
| Absolute Exposure | \|signed_exposure\| | ✅ |
| Quantity Exposure | \|qty_diff × source_b_unit_price\| | ✅ |
| Price Exposure | \|price_diff × source_a_quantity\| | ✅ |
| Amount Exposure | max(absolute − quantity − price, 0) | ✅ |
| Unresolved Exposure | Full amount for UNRESOLVED/MISSING statuses | ✅ |
| Review Exposure | absolute_exposure where review_required = Y | ✅ |

### 7.2 Language Requirements

- Exposure must **never** be labeled as fraud, loss, or theft
- Approved terminology: *exception exposure*, *unreconciled exposure*, *review exposure*, *potential financial discrepancy*
- Directional language (deficit, surplus) must be avoided

---

## 8. Anomaly Detection Requirements

### 8.1 Detection Rules

7 rules must be implemented:

| # | Rule | Severity | Trigger |
|---|---|---|---|
| 1 | HIGH_VALUE_OUTLIER | HIGH | absolute_exposure > mean × 5.0 |
| 2 | LOW_CONFIDENCE_MATCH | MEDIUM | 0 < confidence < 75 |
| 3 | DATA_QUALITY_FAILURE | CRITICAL | status = DATA_QUALITY_EXCEPTION |
| 4 | MASTER_DATA_MISSING | HIGH | status = MASTER_DATA_EXCEPTION |
| 5 | DUPLICATE_KEY | HIGH | status = DUPLICATE_KEY |
| 6 | UNRESOLVED_TRANSACTION | MEDIUM | status = UNRESOLVED |
| 7 | MISSING_COUNTERPART | LOW | status ∈ {MISSING_IN_SOURCE_A, MISSING_IN_SOURCE_B} |

### 8.2 Separation Requirement

Anomaly detection must be independent of reconciliation status. A matched transaction may carry anomalies, and an unmatched transaction may have none.

### 8.3 Multi-rule Requirement

A single line may trigger multiple anomaly rules simultaneously.

---

## 9. Review Queue Requirements

### 9.1 Priority Levels

| Priority | Assignment Rule |
|---|---|
| CRITICAL | DATA_QUALITY_EXCEPTION or DUPLICATE_KEY status |
| HIGH | MASTER_DATA_EXCEPTION or UNRESOLVED with exposure > 1,000; or MISSING_IN_SOURCE_* with exposure > 500 |
| MEDIUM | MASTER_DATA_EXCEPTION/UNRESOLVED with exposure ≤ 1,000; or MISSING_IN_SOURCE_* with exposure ≤ 500 |
| LOW | All other review-required items |

CRITICAL anomaly flags must upgrade any line to CRITICAL priority.

### 9.2 Sorting Requirement

The queue must be sorted by priority (CRITICAL → LOW), then by absolute exposure descending within each priority.

---

## 10. KPI Requirements

### 10.1 Summary KPIs

10 KPIs must be computed: total_lines, matched_lines, exception_lines, match_rate_pct, exception_rate_pct, total_absolute_exposure, unresolved_exposure, average_confidence, review_required_count, review_rate_pct.

### 10.2 Dimensional Breakdowns

The same 10 KPIs must be available by branch and by month.

### 10.3 Output Requirements

- KPIs must be written to CSV (summary, by branch, by month)
- KPIs must be included in dashboard_data.json

---

## 11. Reporting Requirements

| Output | Format | Description |
|---|---|---|
| reconciliation_results.csv | CSV | All reconciliation line pairs with component statuses and exposure |
| data_quality_issues.csv | CSV | All DQ issues with severity and description |
| anomaly_results.csv | CSV | All anomalies with type, severity, and description |
| review_queue.csv | CSV | Prioritized review items |
| kpi_summary.csv | CSV | Top-level KPIs |
| kpi_by_branch.csv | CSV | Per-branch KPIs |
| kpi_by_month.csv | CSV | Per-month KPIs |
| dashboard_data.json | JSON | Consolidated payload for dashboard consumption |

All CSV files must use: UTF-8 encoding, LF line endings, no BOM, fixed 2-decimal float formatting, no index column.

---

## 12. Privacy-by-Design Principles

| # | Principle | Implementation |
|---|---|---|
| 1 | No real data | All data is synthetic, generated with a fixed random seed |
| 2 | No real identifiers | Product IDs, branch IDs, employee IDs are fictional (PRD-xxxx, BR-xxx, EMP-xxxx) |
| 3 | No real names | Product names use fictional brand prefixes (ZENITH, AURORA, NEXUS, etc.) |
| 4 | No real locations | Branch names use fictional cities (Northport, Eastvale, etc.) |
| 5 | Generic source labels | Source systems labeled generically (SOURCE_A, SOURCE_B, POS System, Reference System) |
| 6 | No company branding | No real company logos, trademarks, or internal system names |
| 7 | Reproducibility | Fixed random seed ensures data generation is deterministic and auditable |
| 8 | Manifest verification | SHA-256 fingerprints of all generated files enable tamper detection |
| 9 | Neutral exposure language | Exposure metrics use neutral terminology (never fraud/loss) |
| 10 | Documentation clarity | All documentation explicitly states that data is synthetic |

---

## 13. Acceptance Criteria

| # | Criterion | Verification Method |
|---|---|---|
| 1 | Pipeline completes end-to-end without error | `run_pipeline()` returns valid result |
| 2 | All 8 output files are produced | File existence check |
| 3 | Match results cover all 8 match methods | Distinct `match_method` values in results |
| 4 | All 17 reconciliation statuses are exercised | Ground-truth scenario coverage |
| 5 | Exposure is non-negative | `absolute_exposure ≥ 0` for all lines |
| 6 | Review queue is priority-ordered | Non-decreasing priority sort verification |
| 7 | Deterministic output | Byte-identical files on repeated runs |
| 8 | Test suite passes | `pytest tests/ -v` with zero failures |
| 9 | All KPIs in valid ranges | Programmatic range checks |
| 10 | Ground truth alignment | ≥80% of CLEAN_EXACT_MATCH scenarios resolve to MATCHED |
