# Power BI Data Model — Star Schema Documentation

> Transaction Reconciliation & Anomaly Detection Analytics — Power BI Semantic Model

---

## 1. Overview

The Power BI data model follows a **star schema** design pattern optimised for analytical query performance and DAX measure simplicity. The central **fact table** (`reconciliation_results`) records every matched/unmatched line-pair between Source A (POS) and Source B (Reference System), surrounded by **dimension tables** that provide filtering, grouping, and labelling context.

All data is **synthetic** and loaded from CSV files via Power Query. No live database connections are used.

### Design Principles

| Principle | Application |
|---|---|
| **Single fact table** | All reconciliation outcomes live in one fact; avoids ambiguity in filter context |
| **Surrogate keys** | Integer keys (`product_id`, `branch_id`, `employee_id`) link facts to dimensions — no string joins |
| **Date dimension** | A dedicated calendar table enables time-intelligence DAX (YTD, MTD, rolling averages) |
| **Lookup tables** | Small decode tables for `match_method` and `reconciliation_status` keep the fact table narrow |
| **1:Many relationships** | Every relationship flows from dimension (1-side) → fact (many-side); all are single-direction |

---

## 2. Model Diagram (Logical)

```
                        ┌──────────────────┐
                        │   date_dim       │
                        │  (date PK,       │
                        │   month_key,     │
                        │   year, quarter) │
                        └────────┬─────────┘
                                 │ 1:*
                                 ▼
┌──────────────┐    ┌───────────────────────────────────────────┐    ┌──────────────────┐
│ product_     │    │          reconciliation_results            │    │  match_method_   │
│ master       │1:* │  (fact — one row per A↔B line pair)       │*:1 │  lookup          │
│              ├────►                                           ◄────┤                  │
│ product_id PK│    │ source_a_line_id      source_b_line_id    │    │ match_method PK  │
│ product_code │    │ source_a_transaction_id  source_b_trans.. │    │ match_method_lbl │
│ barcode      │    │ match_method          confidence_score    │    └──────────────────┘
│ product_name │    │ identity_status       quantity_status      │
│ generic_name │    │ price_status          amount_status        │    ┌──────────────────┐
│ brand        │    │ reconciliation_status review_required      │    │  reconcili-      │
│ category     │    │ quantity_difference   price_difference     │    │  ation_status_   │
│ strength     │    │ amount_difference     signed_exposure      │    │  lookup          │
│ reference_   │    │ absolute_exposure     unresolved_exposure  │    │                  │
│  unit_price  │    │ review_exposure       amount_exposure      │    │ reconciliation_  │
└──────────────┘    │ quantity_exposure     price_exposure       │    │  status PK       │
                    │ source_a_amount       source_b_amount      │    │ status_label     │
┌──────────────┐    └───────────────┬───────────────────────────┘    │ status_color     │
│ branch_      │                    │                               └──────────────────┘
│ master       │1:*                 │ 1:*
│              ├────────────────────┘
│ branch_id PK │                    │
│ branch_name  │                    │
│ city         │                    │
│ region       │                    │
└──────┬───────┘                    │
       │ 1:*                        │
       ▼                            ▼
┌──────────────┐           ┌──────────────────┐
│ employee_    │           │  (fact filters    │
│ master       │1:*        │   through         │
│              ├──────────►│   branch_id)      │
│ employee_id  │           │                  │
│ employee_lbl │           └──────────────────┘
│ branch_id FK │
└──────────────┘
```

---

## 3. Fact Table — `reconciliation_results`

| Column | Data Type | Description |
|---|---|---|
| `source_a_line_id` | Text | Unique identifier of the Source A transaction line |
| `source_a_transaction_id` | Text | Parent transaction header ID from Source A |
| `source_b_line_id` | Text | Unique identifier of the Source B transaction line (blank if unmatched) |
| `source_b_transaction_id` | Text | Parent transaction header ID from Source B (blank if unmatched) |
| `match_method` | Text | How the pair was matched: `exact`, `barcode`, `fuzzy_name`, `manual`, `unmatched` |
| `confidence_score` | Decimal (0–1) | Matching confidence; 1.0 for exact, <1 for fuzzy |
| `identity_status` | Text | Product identity match result: `matched`, `near_match`, `mismatch`, `missing` |
| `quantity_status` | Text | Quantity comparison: `equal`, `minor_diff`, `major_diff`, `missing` |
| `price_status` | Text | Unit price comparison: `equal`, `minor_diff`, `major_diff`, `missing` |
| `amount_status` | Text | Line-amount comparison: `equal`, `minor_diff`, `major_diff`, `missing` |
| `reconciliation_status` | Text | Overall outcome: `matched`, `partial`, `exception`, `unmatched_a`, `unmatched_b` |
| `review_required` | Boolean | TRUE if the line needs manual review |
| `quantity_difference` | Integer | Source A quantity minus Source B quantity |
| `price_difference` | Decimal | Source A unit price minus Source B unit price |
| `amount_difference` | Decimal | Source A amount minus Source B amount |
| `source_a_amount` | Decimal | Transaction line amount from Source A |
| `source_b_amount` | Decimal | Transaction line amount from Source B |
| `signed_exposure` | Decimal | `amount_difference` — positive = overcharge, negative = undercharge |
| `absolute_exposure` | Decimal | ABS of signed exposure |
| `quantity_exposure` | Decimal | Financial impact of quantity mismatches |
| `price_exposure` | Decimal | Financial impact of unit-price mismatches |
| `amount_exposure` | Decimal | Financial impact of amount-level mismatches |
| `unresolved_exposure` | Decimal | Exposure from unmatched/exception lines |
| `review_exposure` | Decimal | Exposure carried by lines flagged for review |
| `transaction_date` | Date | Date of the transaction (used to join to `date_dim`) |
| `branch_id` | Integer | Branch surrogate key (joins to `branch_master`) |
| `employee_id` | Integer | Employee surrogate key (joins to `employee_master`) |
| `product_id` | Integer | Product surrogate key (joins to `product_master`) |
| `category` | Text | Product category denormalised for quick filtering |

**Row count estimate:** 10 000–50 000 synthetic rows (depends on scenario generation).

**Granularity:** One row per reconciled line-pair (or unmatched line).

---

## 4. Dimension Tables

### 4.1 `product_master`

| Column | Data Type | Key | Description |
|---|---|---|---|
| `product_id` | Integer | **PK** | Surrogate key |
| `product_code` | Text | | Business product code |
| `barcode` | Text | | EAN / UPC barcode |
| `product_name` | Text | | Full product name |
| `generic_name` | Text | | Generic / INN name |
| `brand` | Text | | Brand or manufacturer |
| `category` | Text | | Product category (used in slicers) |
| `strength` | Text | | Dosage strength |
| `reference_unit_price` | Decimal | | Expected / master-list unit price |

**Relationship:** `product_master[product_id]` 1:* `reconciliation_results[product_id]`

---

### 4.2 `branch_master`

| Column | Data Type | Key | Description |
|---|---|---|---|
| `branch_id` | Integer | **PK** | Surrogate key |
| `branch_name` | Text | | Human-readable branch name |
| `city` | Text | | City where branch operates |
| `region` | Text | | Geographic region (for map visuals) |

**Relationship:** `branch_master[branch_id]` 1:* `reconciliation_results[branch_id]`

---

### 4.3 `employee_master`

| Column | Data Type | Key | Description |
|---|---|---|---|
| `employee_id` | Integer | **PK** | Surrogate key |
| `employee_label` | Text | | Display name / label |
| `branch_id` | Integer | **FK** | Branch assignment |

**Relationships:**
- `employee_master[employee_id]` 1:* `reconciliation_results[employee_id]`
- `branch_master[branch_id]` 1:* `employee_master[branch_id]` (snowflake for employee→branch drill-down)

---

### 4.4 `date_dim`

Generated entirely in Power Query or DAX; not sourced from CSV.

| Column | Data Type | Key | Description |
|---|---|---|---|
| `date` | Date | **PK** | Calendar date (joins to `reconciliation_results[transaction_date]`) |
| `month_key` | Text | | `YYYYMM` format — used for trend sorting |
| `year` | Integer | | Calendar year |
| `quarter` | Text | | `Q1`–`Q4` |
| `month_name` | Text | | `Jan`–`Dec` |
| `month_number` | Integer | | 1–12 |
| `day_of_week` | Text | | `Mon`–`Sun` |
| `is_weekend` | Boolean | | TRUE for Sat/Sun |
| `fiscal_year` | Integer | | Aligns to organisation fiscal year |
| `fiscal_quarter` | Text | | Fiscal quarter label |

**Relationship:** `date_dim[date]` 1:* `reconciliation_results[transaction_date]`

**Mark as date table:** In Power BI, set `date_dim[date]` as the **Date Table** with `date` as the unique date column to enable built-in time-intelligence.

---

### 4.5 `match_method_lookup`

| Column | Data Type | Key | Description |
|---|---|---|---|
| `match_method` | Text | **PK** | Code: `exact`, `barcode`, `fuzzy_name`, `manual`, `unmatched` |
| `match_method_label` | Text | | Human-friendly: `Exact ID Match`, `Barcode Match`, `Fuzzy Name Match`, `Manual Review`, `Unmatched` |
| `sort_order` | Integer | | Display order in charts (exact first, unmatched last) |

**Relationship:** `match_method_lookup[match_method]` 1:* `reconciliation_results[match_method]`

---

### 4.6 `reconciliation_status_lookup`

| Column | Data Type | Key | Description |
|---|---|---|---|
| `reconciliation_status` | Text | **PK** | Code: `matched`, `partial`, `exception`, `unmatched_a`, `unmatched_b` |
| `status_label` | Text | | Human-friendly label |
| `status_color` | Text | | Hex colour for conditional formatting: `#16a34a` (matched), `#eab308` (partial), `#dc2626` (exception), `#64748b` (unmatched) |

**Relationship:** `reconciliation_status_lookup[reconciliation_status]` 1:* `reconciliation_results[reconciliation_status]`

---

## 5. Relationships Summary

| From (1-side) | To (many-side) | Column | Cross-filter | Active |
|---|---|---|---|---|
| `product_master` | `reconciliation_results` | `product_id` | Single | Yes |
| `branch_master` | `reconciliation_results` | `branch_id` | Single | Yes |
| `employee_master` | `reconciliation_results` | `employee_id` | Single | Yes |
| `date_dim` | `reconciliation_results` | `date` / `transaction_date` | Single | Yes |
| `match_method_lookup` | `reconciliation_results` | `match_method` | Single | Yes |
| `reconciliation_status_lookup` | `reconciliation_results` | `reconciliation_status` | Single | Yes |
| `branch_master` | `employee_master` | `branch_id` | Single | Yes |

> **Why single-direction?** All analytics flow from dimension filters into the fact. No fact-to-dimension filter propagation is needed, which prevents ambiguous filter paths and keeps DAX measures deterministic.

---

## 6. Supporting Tables (Not in Star Schema)

These tables feed Power Query transformations but are **not** directly modelled as star-schema members. They are consumed during ETL to enrich the fact table:

| Table | Purpose in Model |
|---|---|
| `source_a_transaction_headers` | Provides `transaction_date`, `branch_id`, `employee_id` — merged into fact during ETL |
| `source_b_transaction_headers` | Same as above, for Source B |
| `source_a_transaction_lines` | Provides `product_id`, `product_code`, amounts — merged into fact |
| `source_b_transaction_lines` | Same as above, for Source B |
| `data_quality_issues` | Reference table for quality annotations; not directly related to fact |
| `anomaly_results` | Standalone analytical output; may be added as a secondary fact in future |
| `review_queue` | Operational table for manual review workflow; linked via `reconciliation_status` |
| `kpi_summary` | Pre-aggregated KPI table used for validation, not for visuals |
| `expected_scenarios` | Test-scenario definitions; not loaded into the model |

---

## 7. Model Optimisation Notes

| Technique | Detail |
|---|---|
| **Column encoding** | Set `branch_id`, `product_id`, `employee_id` as **Integer** in Power Query; avoids dictionary overhead |
| **Date table marking** | Mark `date_dim` as the official date table so `TOTALYTD`, `TOTALMTD`, `SAMEPERIODLASTYEAR` work without workarounds |
| **Hide FK columns** | Hide `branch_id`, `product_id`, `employee_id` in the fact from report view — users interact via dimension names |
| **Sort by column** | Set `match_method_lookup[match_method_label]` **Sort by** `sort_order`; same for `date_dim[month_name]` → `month_number` |
| **Calculated table for date_dim** | Use `CALENDARAUTO()` in DAX or generate in Power Query from the min/max dates in the fact |
| **Relationships only** | No bidirectional or many-to-many relationships — keeps the model simple and fast |

---

## 8. Data Lineage

```
CSV Files (data/raw/)
  │
  ▼
Power Query (Transform)
  ├── Promote headers, type casting
  ├── Merge headers → lines (enrich with date, branch, employee)
  ├── Build reconciliation_results from pipeline output
  ├── Generate date_dim via CALENDARAUTO()
  ├── Create lookup tables (distinct values from fact columns)
  └── Load to model
        │
        ▼
  Star Schema (Semantic Model)
        │
        ▼
  DAX Measures & Report Visuals
```

---

*Document version: 1.0 | Last updated: 2026-09-02 | Project: Transaction Reconciliation & Anomaly Detection Analytics*
