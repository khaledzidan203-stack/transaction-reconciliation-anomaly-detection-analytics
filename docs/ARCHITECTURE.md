# Architecture

## Overview

The Transaction Reconciliation & Anomaly Detection Analytics pipeline is a deterministic, modular Python system that reconciles transaction data across two source systems using an 8-level hierarchical matching engine, computes financial exposure, detects anomalies, and produces KPIs and a prioritized review queue.

Every run produces byte-identical output given the same input, enforced by a fixed random seed (`RANDOM_SEED = 20260902`) and deterministic IO routines.

---

## Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│ Step 1: DATA GENERATION (synthetic_data_generator.py)                   │
│                                                                         │
│  RANDOM_SEED=20260902 → 150 products, 10 branches, 32 employees        │
│  28 scenario types × SCENARIO_COUNTS → Source A/B CSVs + ground truth   │
│  Generation manifest with SHA-256 fingerprints                          │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ Step 2: INGESTION (ingestion.py)                                        │
│                                                                         │
│  load_csvs(data_dir) → RawDataset                                       │
│  ├── product_master, branch_master, employee_master                     │
│  ├── source_a_headers, source_a_lines                                   │
│  ├── source_b_headers, source_b_lines                                   │
│  └── expected_scenarios                                                 │
│                                                                         │
│  Adds normalized key columns:                                            │
│  _norm_product_name, _norm_barcode, _norm_product_code,                 │
│  _norm_reference_id, _norm_txn_id                                       │
│  _qty_float, _price_float, _amount_float                                │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                     ┌───────────┴───────────┐
                     ▼                       ▼
┌──────────────────────────────┐ ┌────────────────────────────────────────┐
│ Step 3: SCHEMA VALIDATION    │ │ Step 4: DATA QUALITY                   │
│ (schema_validation.py)       │ │ (data_quality.py)                      │
│                              │ │                                        │
│ 7 tables validated against   │ │ Duplicate key detection                │
│ EXPECTED_COLUMNS             │ │ Malformed identifier detection         │
│                              │ │ Invalid numeric detection              │
│ Issues: MISSING_COLUMN       │ │ Missing value detection                │
│         UNEXPECTED_COLUMN    │ │ Missing master record detection        │
│                              │ │                                        │
│ Severity: ERROR / WARNING    │ │ Severity: ERROR / WARNING /            │
│                              │ │          BUSINESS_ANOMALY              │
└──────────────────────────────┘ └────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ Step 5: MASTER MAPPING (master_mapping.py)                              │
│                                                                         │
│  build_master_maps(dataset) → MasterMaps                                │
│  ├── product_by_id          [product_id → record]                       │
│  ├── product_by_barcode     [barcode → record]                          │
│  ├── product_by_code        [product_code → record]                     │
│  ├── product_by_norm_name   [normalized_name → [records]]               │
│  ├── product_by_generic     [generic_name → [records]]                  │
│  ├── branch_by_id           [branch_id → record]                        │
│  └── employee_by_id         [employee_id → record]                      │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ Step 6: MATCHING ENGINE (matching.py)                                   │
│                                                                         │
│  match_lines(a_lines, b_lines) → match_results DataFrame                │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ 8-Level Hierarchy (first match wins)                            │    │
│  │                                                                 │    │
│  │ 1. EXACT_PRIMARY_ID      ── A.reference_id = B.transaction_id  │    │
│  │                            AND A.product_id  = B.product_id     │    │
│  │ 2. EXACT_BARCODE         ── Normalized barcode equality         │    │
│  │ 3. EXACT_PRODUCT_CODE    ── Normalized product code equality    │    │
│  │ 4. NORMALIZED_NAME       ── Deterministic name key equality     │    │
│  │ 5. FUZZY_NAME            ── Token-sort/partial ratio ≥ 0.80    │    │
│  │ 6. GENERIC_STRENGTH      ── Same generic+strength, diff brand  │    │
│  │ 7. POSSIBLE_SUBSTITUTE   ── Fuzzy generic match ≥ 0.70         │    │
│  │ 8. UNMATCHED             ── No match found                      │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  Performance: Inverted token index for fuzzy candidate retrieval         │
│  Consumption: B-lines marked as consumed to prevent duplicate matching  │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ Step 7: RECONCILIATION (reconciliation.py)                              │
│                                                                         │
│  reconcile(match_results, a_lines, b_lines, a_headers, b_headers)       │
│  → reconciliation_results DataFrame                                     │
│                                                                         │
│  Component Status Derivation:                                           │
│  ┌────────────────┬──────────────────────────────────────────────────┐  │
│  │ Identity       │ MATCHED / SUBSTITUTE / UNMATCHED / MISSING_A/B   │  │
│  │ Quantity       │ MATCHED / SHORTAGE / EXCESS / NOT_APPLICABLE     │  │
│  │ Price          │ MATCHED / VARIANCE / NOT_APPLICABLE              │  │
│  │ Amount         │ MATCHED / VARIANCE / NOT_APPLICABLE              │  │
│  └────────────────┴──────────────────────────────────────────────────┘  │
│                                                                         │
│  Overall Status: derived from component combination                     │
│  17 statuses (MATCHED → UNRESOLVED)                                     │
│  Tolerances: price ±0.01, amount ±0.02, quantity ±0.0001               │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ Step 8: EXPOSURE (exposure.py)                                          │
│                                                                         │
│  compute_exposure(recon_results) → enhanced DataFrame                   │
│                                                                         │
│  signed_exposure    = source_a_amount − source_b_amount                 │
│  absolute_exposure  = |signed_exposure|                                 │
│  quantity_exposure  = |qty_diff × source_b_unit_price|                  │
│  price_exposure     = |price_diff × source_a_quantity|                  │
│  amount_exposure    = max(absolute − quantity − price, 0)               │
│  unresolved_exposure = full amount for UNRESOLVED / MISSING statuses    │
│  review_exposure    = absolute_exposure where review_required = 'Y'     │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                     ┌───────────┴───────────┐
                     ▼                       ▼
┌──────────────────────────────┐ ┌────────────────────────────────────────┐
│ Step 9: ANOMALY DETECTION    │ │ Step 10: KPI COMPUTATION               │
│ (anomaly_detection.py)       │ │ (kpis.py)                              │
│                              │ │                                        │
│ 7 Rules:                     │ │ compute_kpis() → 10 summary metrics    │
│  HIGH_VALUE_OUTLIER          │ │ compute_kpis_by_branch() → per branch  │
│  LOW_CONFIDENCE_MATCH        │ │ compute_kpis_by_month() → per month    │
│  DATA_QUALITY_FAILURE        │ │                                        │
│  MASTER_DATA_MISSING         │ │ match_rate_pct, exception_rate_pct,    │
│  DUPLICATE_KEY               │ │ total_absolute_exposure,               │
│  UNRESOLVED_TRANSACTION      │ │ unresolved_exposure, avg_confidence,   │
│  MISSING_COUNTERPART         │ │ review_required_count, review_rate_pct │
│                              │ │                                        │
│ Severity: CRITICAL / HIGH /  │ │                                        │
│           MEDIUM / LOW       │ │                                        │
└──────────────────────────────┘ └────────────────────────────────────────┘
                     │                       │
                     └───────────┬───────────┘
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ Step 11: REVIEW QUEUE + REPORTING                                       │
│                                                                         │
│ build_review_queue(recon, anomalies) → prioritized queue                │
│   Priority: CRITICAL → HIGH → MEDIUM → LOW                             │
│   Sorted: priority ascending, exposure descending                       │
│                                                                         │
│ write_all_outputs() → 8 CSV files + 1 JSON:                            │
│   reconciliation_results.csv                                            │
│   data_quality_issues.csv                                               │
│   anomaly_results.csv                                                   │
│   review_queue.csv                                                      │
│   kpi_summary.csv                                                       │
│   kpi_by_branch.csv                                                     │
│   kpi_by_month.csv                                                      │
│   dashboard_data.json                                                   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Module Dependency Graph

```
pipeline.py
├── ingestion.py
│   ├── config.py
│   └── normalization.py
├── schema_validation.py
│   └── config.py
├── data_quality.py
│   ├── config.py
│   └── normalization.py
├── master_mapping.py
│   └── normalization.py
├── matching.py
│   ├── config.py
│   ├── normalization.py
│   └── rapidfuzz (external)
├── reconciliation.py
│   └── config.py
├── exposure.py
│   └── config.py
├── anomaly_detection.py
│   └── config.py
├── kpis.py
│   ├── config.py
│   └── normalization.py
├── review_queue.py
│   └── config.py
└── reporting.py
    ├── config.py
    └── utils.py

synthetic_data_generator.py
├── config.py
├── normalization.py
└── utils.py
```

---

## Data Flow

```
                    ┌─────────────────┐
                    │  CSV Files on   │
                    │  Disk (data/)   │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │   RawDataset    │
                    │  (ingestion.py) │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
     ┌────────────┐  ┌────────────┐  ┌────────────┐
     │ Schema DQ  │  │ Content DQ │  │Master Maps │
     └────────────┘  └────────────┘  └────────────┘
                             │
                    ┌────────▼────────┐
                    │ Match Results   │
                    │ (matching.py)   │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ Reconciliation  │
                    │ Results         │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ + Exposure      │
                    │ Columns         │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
     ┌────────────┐  ┌────────────┐  ┌────────────┐
     │ Anomalies  │  │   KPIs     │  │Review Queue│
     └────────────┘  └────────────┘  └────────────┘
                             │
                    ┌────────▼────────┐
                    │  Output Files   │
                    │  (CSV + JSON)   │
                    └─────────────────┘
```

---

## Matching Hierarchy Detail

The matching engine processes each Source A line against Source B lines using a strict hierarchy. The first level that produces a match determines the result; lower levels are not attempted.

```
Source A Line
     │
     ▼
┌──────────────────────────────────────────────────┐
│ Level 1: EXACT_PRIMARY_ID                        │
│   A._norm_reference_id == B._norm_txn_id         │
│   AND A.product_id == B.product_id               │
│   → confidence: 100                              │
├──────────────────────────────────────────────────┤
│ Level 2: EXACT_BARCODE                           │
│   A._norm_barcode == B._norm_barcode             │
│   (non-empty)                                    │
│   → confidence: 97                               │
├──────────────────────────────────────────────────┤
│ Level 3: EXACT_PRODUCT_CODE                      │
│   A._norm_product_code == B._norm_product_code   │
│   (non-empty)                                    │
│   → confidence: 95                               │
├──────────────────────────────────────────────────┤
│ Level 4: NORMALIZED_NAME                         │
│   A._norm_product_name == B._norm_product_name   │
│   (non-empty)                                    │
│   → confidence: 90                               │
├──────────────────────────────────────────────────┤
│ Level 5: FUZZY_NAME                              │
│   Token index candidate retrieval                │
│   max(token_sort_ratio, partial_ratio)            │
│   ≥ 0.92 → ACCEPT band (confidence = score×100)  │
│   0.80–0.92 → REVIEW band                        │
│   < 0.80 → no match at this level                │
├──────────────────────────────────────────────────┤
│ Level 6: GENERIC_STRENGTH                        │
│   Same generic_name key, different product_name   │
│   → confidence: 85                               │
├──────────────────────────────────────────────────┤
│ Level 7: POSSIBLE_SUBSTITUTE                     │
│   Fuzzy generic match ≥ 0.70                     │
│   → confidence: 70                               │
├──────────────────────────────────────────────────┤
│ Level 8: UNMATCHED                               │
│   No match found                                 │
│   → confidence: 0                                │
└──────────────────────────────────────────────────┘
```

**B-line consumption:** Once a Source B line is matched to a Source A line, it is removed from the candidate pool for all subsequent Source A lines. This prevents many-to-one matches.

---

## Status Derivation Logic

Reconciliation status is derived from four independent component statuses:

```
┌───────────────┐    ┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│   Identity    │    │   Quantity    │    │    Price      │    │    Amount     │
│   Status      │    │   Status      │    │    Status     │    │    Status     │
└───────┬───────┘    └───────┬───────┘    └───────┬───────┘    └───────┬───────┘
        │                    │                    │                    │
        └────────────────────┴────────────────────┴────────────────────┘
                                     │
                                     ▼
                        ┌────────────────────────┐
                        │  Derivation Rules      │
                        │                        │
                        │ 1. CREDIT/REVERSAL     │
                        │    → immediate return  │
                        │ 2. Unmatched side      │
                        │    → MISSING_*         │
                        │ 3. Fuzzy < 80          │
                        │    → FUZZY_MATCH_REVIEW│
                        │ 4. IDENTITY_UNMATCHED  │
                        │    → UNRESOLVED        │
                        │ 5. Qty AND Amt issue   │
                        │    → QTY_AND_AMT_DIFF  │
                        │ 6. Qty issue only      │
                        │    → QUANTITY_DIFFERENCE│
                        │ 7. Price issue only    │
                        │    → PRICE_DIFFERENCE  │
                        │ 8. Amt issue only      │
                        │    → AMOUNT_DIFFERENCE │
                        │ 9. IDENTITY_SUBSTITUTE │
                        │    → MATCHED_W_SUB     │
                        │ 10. Otherwise          │
                        │    → MATCHED           │
                        └────────────────────────┘
```

---

## Key Design Principles

1. **Determinism** — Fixed random seed, deterministic IO (LF line endings, UTF-8 no BOM, fixed decimal formatting), SHA-256 manifest verification
2. **Explainability** — Every match result includes method, confidence, and fuzzy score; every reconciliation result includes 4 component statuses
3. **Separation of concerns** — Each module has a single responsibility; the pipeline orchestrates without coupling
4. **Ground truth** — 28 controlled scenarios with known expected outcomes enable regression testing
5. **Privacy by design** — No real data; all identifiers, names, and amounts are fictional
6. **No magic numbers** — Every threshold, tolerance, and multiplier is defined in `config.py` with documentation
