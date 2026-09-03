# Transaction Reconciliation & Anomaly Detection Analytics

> A portfolio-grade analytics project demonstrating multi-source transaction reconciliation, explainable hierarchical matching, anomaly detection, exception management, financial exposure analysis, and KPI reporting — built entirely with deterministic synthetic data.

---

## Executive Summary

This project implements a complete analytical pipeline for reconciling transaction data across two source systems (a POS system and a Reference system). It demonstrates production-style data engineering, an 8-level explainable matching engine, rule-based anomaly detection, financial exposure decomposition, and KPI reporting — all built with fully synthetic data for portfolio demonstration purposes.

**This project uses fully synthetic data created specifically for portfolio demonstration purposes. It does not contain real customer, employee, transaction, company, or proprietary business data.**

---

## Key Features

- **Deterministic synthetic data generation** — 150 products, 10 branches, 32 employees, 2,200+ transactions across 4 months with a fixed random seed (`20260902`)
- **8-level hierarchical matching engine** — transparent, explainable match decisions with confidence scores from 100 to 0
- **28 controlled injection scenarios** — ground-truth tagged data covering every match level, variance type, and data quality exception
- **4-component reconciliation** — identity, quantity, price, and amount statuses derived independently; overall status derived from components
- **17 reconciliation statuses** — from `MATCHED` through `UNRESOLVED`, covering variances, credits, reversals, and data quality blocks
- **Financial exposure decomposition** — signed, absolute, quantity, price, amount, unresolved, and review exposure
- **7 rule-based anomaly detectors** — severity-graded (LOW / MEDIUM / HIGH / CRITICAL) anomaly flagging
- **Prioritized review queue** — CRITICAL / HIGH / MEDIUM / LOW priority based on status, exposure, and anomaly flags
- **KPI framework** — summary, by-branch, and by-month metrics with configurable thresholds
- **Full reproducibility** — byte-identical output on every run; SHA-256 manifest verification

---

## Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                     Synthetic Data Generator                       │
│   150 products · 10 branches · 32 employees · 2,200+ txns        │
│   28 scenario types with ground truth · Fixed seed 20260902       │
└──────────────┬─────────────────────────────────────────────────────┘
               │ CSV files (product_master, branch_master, etc.)
               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Ingestion Layer                              │
│   load_csvs() → RawDataset with normalized key columns             │
│   _norm_product_name · _norm_barcode · _norm_product_code          │
│   _qty_float · _price_float · _amount_float                        │
└──────────────┬──────────────────────────────────────────────────────┘
               │
       ┌───────┴────────┐
       ▼                ▼
┌──────────────┐ ┌───────────────────┐
│Schema        │ │Data Quality       │
│Validation    │ │Engine             │
│7 tables ·    │ │Duplicate keys     │
│column checks │ │Malformed IDs      │
│              │ │Invalid numerics   │
│              │ │Missing master refs│
└──────────────┘ └───────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Master Mapping Layer                              │
│   product_by_id · product_by_barcode · product_by_code             │
│   product_by_norm_name · product_by_generic                        │
│   branch_by_id · employee_by_id                                    │
└──────────────┬──────────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────────┐
│               8-Level Matching Engine                               │
│                                                                    │
│  1. EXACT_PRIMARY_ID      (confidence: 100)                        │
│  2. EXACT_BARCODE         (confidence:  97)                        │
│  3. EXACT_PRODUCT_CODE    (confidence:  95)                        │
│  4. NORMALIZED_NAME       (confidence:  90)                        │
│  5. FUZZY_NAME            (confidence: score, accept ≥0.92)        │
│  6. GENERIC_STRENGTH      (confidence:  85)                        │
│  7. POSSIBLE_SUBSTITUTE   (confidence:  70)                        │
│  8. UNMATCHED             (confidence:   0)                        │
│                                                                    │
│  Inverted token index for O(n) fuzzy candidate retrieval           │
└──────────────┬──────────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────────┐
│              Reconciliation Engine                                   │
│                                                                    │
│  Component statuses:  Identity → Quantity → Price → Amount          │
│  Overall status derived from component combination                  │
│  17 statuses · Review routing · Tolerance checks                    │
│  Price ±0.01 · Amount ±0.02 · Quantity ±0.0001                     │
└──────────────┬──────────────────────────────────────────────────────┘
               │
       ┌───────┴────────────┐
       ▼                    ▼
┌──────────────┐  ┌──────────────────┐
│Exposure      │  │Anomaly Detection │
│Computation   │  │7 rules · 4 levels│
│              │  │                  │
│Signed        │  │HIGH_VALUE_OUTLIER│
│Absolute      │  │LOW_CONFIDENCE    │
│Qty / Price / │  │DQ_FAILURE        │
│Amount decom. │  │MASTER_MISSING    │
│Unresolved    │  │DUPLICATE_KEY     │
│Review        │  │UNRESOLVED_TXN    │
│              │  │MISSING_COUNTER   │
└──────┬───────┘  └────────┬─────────┘
       │                   │
       └───────┬───────────┘
               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  Review Queue Builder                                │
│  Priority: CRITICAL / HIGH / MEDIUM / LOW                           │
│  Sorted by priority then exposure descending                        │
└──────────────┬──────────────────────────────────────────────────────┘
               │
       ┌───────┴────────┐
       ▼                ▼
┌──────────────┐ ┌───────────────────┐
│KPI Framework │ │Reporting Layer    │
│              │ │                   │
│Summary       │ │reconciliation_    │
│By branch     │ │  results.csv      │
│By month      │ │data_quality_      │
│              │ │  issues.csv       │
│10 KPIs each  │ │anomaly_results.csv│
│              │ │review_queue.csv   │
│              │ │kpi_*.csv          │
│              │ │dashboard_data.json│
└──────────────┘ └───────────────────┘
```

---

## Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd transaction-reconciliation-anomaly-detection-analytics-portfolio

# Create virtual environment
python -m venv .venv
source .venv/bin/activate   # Linux / macOS
.venv\Scripts\activate      # Windows

# Install dependencies
pip install -r requirements.txt

# Generate synthetic data
python -c "from src.synthetic_data_generator import generate_all; generate_all()"

# Run the full reconciliation pipeline
python -c "from src.pipeline import run_pipeline; run_pipeline()"

# Run the test suite
pytest tests/ -v
```

**Dependencies:** `pandas>=2.0.0`, `numpy>=1.24.0`, `rapidfuzz>=3.0.0`, `pytest>=7.0.0`

---

## Module Descriptions

| Module | Responsibility |
|---|---|
| `src/config.py` | Central configuration: `RANDOM_SEED=20260902`, all constants, 28 scenario types, tolerances, 17 statuses |
| `src/utils.py` | Deterministic IO: `round_money`, `write_csv`, `read_csv`, `file_sha256`, `frame_fingerprint`, `write_json` |
| `src/normalization.py` | Text/identifier/numeric normalization: Unicode NFKC, EAN-13 validation, unit splitting, fuzzy preparation |
| `src/synthetic_data_generator.py` | Deterministic data generation: 150 products, 10 branches, 32 employees, 2K+ transactions, 28 scenarios |
| `src/ingestion.py` | CSV loading with normalized key columns (`_norm_*`, `_*_float`) |
| `src/schema_validation.py` | Column structure validation for 7 input tables |
| `src/data_quality.py` | DQ checks: duplicates, malformed IDs, invalid numerics, missing master refs |
| `src/master_mapping.py` | Product/branch/employee lookup dictionaries (5 product indexes) |
| `src/matching.py` | 8-level hierarchical matcher with inverted token index |
| `src/reconciliation.py` | Component status computation (identity/quantity/price/amount) and overall status derivation |
| `src/exposure.py` | Financial exposure: signed, absolute, qty/price/amount decomposition, unresolved, review |
| `src/anomaly_detection.py` | 7 rule-based anomaly detectors with 4 severity levels |
| `src/kpis.py` | KPI framework: 10 summary metrics, by-branch, by-month breakdowns |
| `src/review_queue.py` | Prioritized review queue: CRITICAL/HIGH/MEDIUM/LOW |
| `src/reporting.py` | Output file writers (8 CSV + 1 JSON) |
| `src/pipeline.py` | End-to-end orchestrator: 11-step pipeline |

---

## Scenario Catalogue

28 controlled scenario types injected with known ground truth:

| # | Scenario Type | Expected Match Method | Expected Reconciliation Status | Review Required |
|---|---|---|---|---|
| 1 | `CLEAN_EXACT_MATCH` | EXACT_PRIMARY_ID | MATCHED | N |
| 2 | `PRIMARY_ID_MATCH` | EXACT_PRIMARY_ID | MATCHED | N |
| 3 | `BARCODE_MATCH` | EXACT_BARCODE | MATCHED | N |
| 4 | `PRODUCT_CODE_MATCH` | EXACT_PRODUCT_CODE | MATCHED | N |
| 5 | `NORMALIZED_NAME_MATCH` | NORMALIZED_NAME | MATCHED | N |
| 6 | `FUZZY_NAME_MATCH` | FUZZY_NAME | MATCHED | N |
| 7 | `GENERIC_STRENGTH_EQUIVALENT` | GENERIC_STRENGTH | MATCHED_WITH_SUBSTITUTE | N |
| 8 | `POSSIBLE_SUBSTITUTE` | POSSIBLE_SUBSTITUTE | MATCHED_WITH_SUBSTITUTE | Y |
| 9 | `MISSING_IN_SOURCE_A` | UNMATCHED | MISSING_IN_SOURCE_A | Y |
| 10 | `MISSING_IN_SOURCE_B` | UNMATCHED | MISSING_IN_SOURCE_B | Y |
| 11 | `ADDITIONAL_TRANSACTION` | UNMATCHED | ADDITIONAL_TRANSACTION | Y |
| 12 | `ADDITIONAL_ITEM` | UNMATCHED | ADDITIONAL_ITEM | Y |
| 13 | `QUANTITY_SHORTAGE` | EXACT_PRIMARY_ID | QUANTITY_DIFFERENCE | Y |
| 14 | `QUANTITY_EXCESS` | EXACT_PRIMARY_ID | QUANTITY_DIFFERENCE | Y |
| 15 | `PRICE_DIFFERENCE` | EXACT_PRIMARY_ID | PRICE_DIFFERENCE | Y |
| 16 | `AMOUNT_DIFFERENCE` | EXACT_PRIMARY_ID | AMOUNT_DIFFERENCE | Y |
| 17 | `QUANTITY_AND_AMOUNT_DIFFERENCE` | EXACT_PRIMARY_ID | QUANTITY_AND_AMOUNT_DIFFERENCE | Y |
| 18 | `CREDIT` | EXACT_PRIMARY_ID | CREDIT | N |
| 19 | `REVERSAL` | EXACT_PRIMARY_ID | REVERSAL | N |
| 20 | `DUPLICATE_TRANSACTION_KEY` | UNMATCHED | DUPLICATE_KEY | Y |
| 21 | `DUPLICATE_LINE` | UNMATCHED | DUPLICATE_KEY | Y |
| 22 | `MISSING_MASTER_RECORD` | UNMATCHED | MASTER_DATA_EXCEPTION | Y |
| 23 | `MALFORMED_IDENTIFIER` | UNMATCHED | DATA_QUALITY_EXCEPTION | Y |
| 24 | `INVALID_NUMERIC` | UNMATCHED | DATA_QUALITY_EXCEPTION | Y |
| 25 | `ABNORMAL_REFERENCE_PRICE` | varies | varies | Y |
| 26 | `HIGH_VALUE_OUTLIER` | varies | varies | Y |
| 27 | `LOW_CONFIDENCE_FUZZY` | FUZZY_NAME | FUZZY_MATCH_REVIEW | Y |
| 28 | `UNRESOLVED` | UNMATCHED | UNRESOLVED | Y |

---

## KPI Definitions

| KPI | Description | Formula |
|---|---|---|
| `total_lines` | Total reconciliation line pairs | `COUNT(*)` |
| `matched_lines` | Lines with MATCHED or MATCHED_WITH_SUBSTITUTE | `COUNT WHERE status ∈ {MATCHED, MATCHED_WITH_SUBSTITUTE}` |
| `exception_lines` | Lines with exception statuses | `COUNT WHERE status ∈ EXCEPTION_STATUSES` |
| `match_rate_pct` | Percentage of lines matched | `(matched_lines / total_lines) × 100` |
| `exception_rate_pct` | Percentage with exceptions | `(exception_lines / total_lines) × 100` |
| `total_absolute_exposure` | Sum of absolute exposure | `SUM(\|signed_exposure\|)` |
| `unresolved_exposure` | Exposure from unresolved cases | `SUM(unresolved_exposure)` |
| `average_confidence` | Mean match confidence | `AVG(confidence_score)` |
| `review_required_count` | Lines flagged for manual review | `COUNT WHERE review_required = 'Y'` |
| `review_rate_pct` | Percentage requiring review | `(review_required_count / total_lines) × 100` |

---

## Privacy & Synthetic Data Statement

**This project uses fully synthetic data created specifically for portfolio demonstration purposes.**

- No real customer, employee, transaction, prescription, company, or proprietary business data is included
- All names, identifiers, codes, amounts, and dates are fictional
- The synthetic data generator uses a fixed random seed (`20260902`) for full reproducibility
- No real company logos, branding, or internal system names are used
- Generic terminology is used throughout (Source System A, Source System B, POS System, Reference System)
- Exposure is never labeled as fraud or loss — terms used: *exception exposure*, *unreconciled exposure*, *review exposure*, *potential financial discrepancy*

---

## Repository Structure

```
├── README.md                           # This file
├── LICENSE                             # MIT License
├── requirements.txt                    # Python dependencies
├── CHANGELOG.md
├── CONTRIBUTING.md
├── SECURITY.md
├── PORTFOLIO_NOTES.md
├── PRIVACY_CHECKLIST.md
├── src/                                # Python analytical engine
│   ├── config.py                       # Central configuration
│   ├── utils.py                        # Deterministic IO helpers
│   ├── normalization.py               # Text/identifier/numeric normalization
│   ├── synthetic_data_generator.py    # Deterministic data generation
│   ├── ingestion.py                   # CSV loading + typed normalization
│   ├── schema_validation.py           # Column structure validation
│   ├── data_quality.py               # DQ checks engine
│   ├── master_mapping.py             # Reference master lookups
│   ├── matching.py                   # 8-level hierarchical matcher
│   ├── reconciliation.py             # Component + overall status
│   ├── exposure.py                   # Financial exposure computation
│   ├── anomaly_detection.py          # Rule-based anomaly flagging
│   ├── kpis.py                       # KPI framework
│   ├── review_queue.py              # Prioritized review queue
│   ├── reporting.py                  # Output file writers
│   └── pipeline.py                  # End-to-end orchestrator
├── tests/                             # Automated test suite
│   ├── conftest.py
│   ├── test_config.py
│   ├── test_utils.py
│   ├── test_normalization.py
│   ├── test_synthetic_data.py
│   ├── test_data_quality.py
│   ├── test_matching.py
│   ├── test_reconciliation.py
│   └── test_pipeline.py
├── data/sample/                       # Synthetic sample data (generated)
├── docs/                              # Documentation
│   ├── ARCHITECTURE.md
│   ├── DATA_DICTIONARY.md
│   ├── MATCHING_METHODOLOGY.md
│   ├── RECONCILIATION_RULES.md
│   ├── EXPOSURE_METHODOLOGY.md
│   ├── ANOMALY_DETECTION.md
│   ├── DATA_QUALITY.md
│   ├── KPI_DICTIONARY.md
│   ├── BUSINESS_REQUIREMENTS.md
│   ├── TEST_CASES.md
│   └── powerbi/
├── sql/                               # SQL analytical queries
├── dashboard/                         # HTML analytical dashboard
└── outputs/examples/                  # Example output files (generated)
```

---

## License

MIT License. See [LICENSE](LICENSE) file.

---

*Built as a portfolio demonstration project. All data is synthetic.*
