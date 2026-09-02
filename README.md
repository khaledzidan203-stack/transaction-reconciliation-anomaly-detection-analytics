# Transaction Reconciliation & Anomaly Detection Analytics

> A portfolio-grade analytics project demonstrating multi-source transaction reconciliation, explainable matching, anomaly detection, exception management, financial exposure analysis, and KPI reporting — built entirely with synthetic data.

---

## Executive Summary

This project implements a complete analytical pipeline for reconciling transaction data across multiple source systems. It demonstrates production-style data engineering, reconciliation logic, anomaly detection, and reporting — all built with fully synthetic data for portfolio demonstration purposes.

**This project uses fully synthetic data created specifically for portfolio demonstration purposes. It does not contain real customer, employee, transaction, prescription, company, or proprietary business data.**

---

## Business Problem

Organizations that process transactions across multiple systems frequently face reconciliation challenges:

- Transactions recorded in one system may be missing, duplicated, or altered in another
- Product identifiers, names, and codes may not align across systems
- Quantities, prices, and amounts may diverge due to timing, rounding, or data-entry errors
- Manual review queues accumulate exceptions that require analyst judgment
- Financial exposure from unreconciled items must be quantified and tracked
- Anomalies in transaction patterns may indicate data quality issues or operational risks

A robust reconciliation framework addresses these challenges through deterministic matching, constrained fuzzy matching, data quality controls, anomaly detection, and transparent exposure calculation.

---

## Project Objectives

1. **Demonstrate multi-source reconciliation** — match transactions across two or more source systems using a transparent, explainable matching hierarchy
2. **Implement data quality engineering** — validate schemas, detect anomalies, flag data quality issues before reconciliation
3. **Build an explainable matching engine** — every match decision is traceable with method, confidence score, and supporting evidence
4. **Calculate financial exposure** — quantify unreconciled amounts by category, branch, employee, and time period
5. **Detect analytical anomalies** — identify unusual patterns in transaction volume, amounts, match rates, and exception concentrations
6. **Generate review queues** — classify exceptions for manual analyst review with priority and context
7. **Produce analytical KPIs** — match rates, exception rates, exposure metrics, trend analysis
8. **Deliver portfolio-grade documentation** — architecture, methodology, data dictionaries, test cases, Power BI design

---

## Why Reconciliation Matters

Reconciliation is a foundational analytical capability across industries:

- **Financial services** — reconcile trades, settlements, and ledger entries
- **Healthcare / pharmacy** — reconcile dispensing records across POS, insurance, and regulatory systems
- **Retail / e-commerce** — reconcile orders, shipments, and payments
- **Telecommunications** — reconcile usage records across billing systems
- **Supply chain** — reconcile inventory movements across warehouses and logistics systems

The analytical patterns are universal: multi-source matching, exception classification, exposure quantification, and anomaly detection.

---

## Architecture

```
Synthetic Source Data
    ↓
Ingestion
    ↓
Schema Validation
    ↓
Normalization
    ↓
Data Quality Checks
    ↓
Reference Master Mapping
    ↓
Matching Engine
    ↓
Quantity / Price / Amount Validation
    ↓
Reconciliation Classification
    ↓
Financial Exposure Calculation
    ↓
Anomaly Detection
    ↓
Exception / Manual Review Queue
    ↓
Analytical KPIs
    ↓
SQL Analysis
    ↓
HTML Dashboard
    ↓
Portfolio Documentation
```

---

## Data Model

| Entity | Grain |
|---|---|
| `transaction_header` | One row per transaction per source system |
| `transaction_line` | One row per transaction item per source system |
| `product_master` | One row per synthetic product |
| `branch_master` | One row per synthetic branch |
| `employee_master` | One row per synthetic employee |
| `reconciliation_result` | One row per reconciled transaction-line comparison |
| `data_quality_issue` | One row per detected DQ issue |
| `anomaly_result` | One row per detected analytical anomaly |
| `review_queue` | One row per unresolved / low-confidence / exception case |

See `docs/DATA_DICTIONARY.md` for full column definitions.

---

## Matching Methodology

The matching engine uses a transparent hierarchy. Each level is attempted in order; the first successful match determines the result.

| Priority | Method | Description |
|---|---|---|
| 1 | Exact Primary ID | Transaction reference number matches exactly |
| 2 | Exact Barcode | Product barcode matches exactly |
| 3 | Exact Product Code | Product master code matches exactly |
| 4 | Normalized Name | Deterministic name normalization produces identical keys |
| 5 | Fuzzy Name | Constrained fuzzy string matching above confidence threshold |
| 6 | Equivalent Product | Same active ingredient / generic strength match |
| 7 | Possible Substitute | Low-confidence match flagged for review |
| 8 | Unmatched | No match found — routed to manual review |

Every result preserves: match method, confidence score, supporting evidence, identity status, quantity status, price status, amount status, reconciliation status, and review flag.

See `docs/MATCHING_METHODOLOGY.md` for full details.

---

## Reconciliation Logic

Standardized reconciliation statuses:

- `MATCHED` — exact or high-confidence match
- `MATCHED_WITH_SUBSTITUTE` — equivalent product matched
- `MISSING_IN_SOURCE_A` — item exists in Source B only
- `MISSING_IN_SOURCE_B` — item exists in Source A only
- `ADDITIONAL_TRANSACTION` — entire transaction exists in one source only
- `ADDITIONAL_ITEM` — individual line item exists in one source only
- `QUANTITY_DIFFERENCE` — matched item with quantity variance
- `PRICE_DIFFERENCE` — matched item with price variance
- `AMOUNT_DIFFERENCE` — matched item with amount variance
- `QUANTITY_AND_AMOUNT_DIFFERENCE` — combined variance
- `CREDIT` — credit-only transaction
- `REVERSAL` — reversal transaction
- `FUZZY_MATCH_REVIEW` — low-confidence match requiring analyst review
- `MASTER_DATA_EXCEPTION` — missing or invalid master data
- `DUPLICATE_KEY` — duplicate transaction detected
- `DATA_QUALITY_EXCEPTION` — data quality issue prevents matching
- `UNRESOLVED` — no classification possible

See `docs/RECONCILIATION_RULES.md` for decision logic.

---

## Anomaly Detection

Analytical anomaly rules detect unusual patterns:

- Unusually high transaction amount
- Unusual quantity or unit price
- Repeated duplicate transactions
- Excessive manual-review rate by branch or employee
- Abnormal credit or reversal frequency
- Repeated quantity or price variance
- Unusually low match confidence
- Abnormal unmatched item count
- Abnormal transaction frequency
- Anomalous exposure concentration

Anomalies are classified by severity: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`.

See `docs/ANOMALY_DETECTION.md` for rule definitions and thresholds.

---

## Exposure Methodology

Financial exposure is calculated transparently:

| Metric | Formula |
|---|---|
| Signed Exposure | Source A amount − Source B amount |
| Absolute Exposure | \|Signed Exposure\| |
| Positive Exposure | MAX(Signed Exposure, 0) |
| Negative Exposure | MIN(Signed Exposure, 0) |
| Quantity Exposure | Source A qty − Source B qty |
| Price Exposure | Source A unit price − Source B unit price |
| Amount Exposure | Source A amount − Source B amount |
| Total Exception Exposure | SUM(\|Amount Exposure\|) for all exceptions |
| Unresolved Exposure | SUM(\|Amount Exposure\|) for UNRESOLVED cases |
| Review Exposure | SUM(\|Amount Exposure\|) for review-required cases |

Exposure is never automatically labeled as fraud or loss. Language used: *exception exposure*, *unreconciled exposure*, *review exposure*, *potential financial discrepancy*.

See `docs/EXPOSURE_METHODOLOGY.md` for full documentation.

---

## Data Quality Controls

DQ categories: `ERROR`, `WARNING`, `BUSINESS_ANOMALY`

Validations:
- Required columns present
- Null / missing value detection
- Data type validation
- Duplicate key detection
- Invalid quantities, prices, amounts
- Negative value detection
- Malformed identifier detection
- Missing master records
- Inconsistent totals
- Inconsistent transaction dates
- Unexpected categories

See `docs/DATA_QUALITY.md` for full validation rules.

---

## KPIs

Key performance indicators include:

- Total transactions / transaction lines
- Match rate, exact match rate, fuzzy match rate, substitute match rate
- Unmatched rate, exception rate, manual review rate
- Duplicate rate
- Quantity / price / amount variance rates
- Credit rate, reversal rate
- Total absolute exposure, signed net exposure, unresolved exposure
- Exposure per transaction
- Exception count by branch / employee
- Exposure concentration
- Top anomaly categories
- Match confidence distribution
- Reconciliation status distribution
- Trend by month / branch

See `docs/KPI_DICTIONARY.md` for definitions, formulas, and interpretation.

---

## Dashboard Overview

The HTML analytical dashboard provides:

1. **Executive Overview** — headline KPIs and status summary
2. **Reconciliation Performance** — match rates and status distribution
3. **Matching Quality** — method distribution and confidence scores
4. **Financial Exposure** — exposure by category and trend
5. **Exception Analysis** — exception types and top reasons
6. **Branch Performance** — exceptions and exposure by branch
7. **Employee Analysis** — exceptions and exposure by employee
8. **Data Quality** — DQ issue summary and trends
9. **Anomaly Detection** — anomalies by severity and category
10. **Manual Review Queue** — pending review cases with context

Dashboard uses only synthetic demo data.

---

## SQL Capabilities

SQL scripts demonstrate analytical queries:

- Schema definition
- Data quality analysis
- Reconciliation summary
- Exposure analysis
- Branch analysis
- Employee analysis
- Anomaly analysis
- Trend analysis
- Exception queue
- Validation queries

See `sql/` directory.

---

## Python Capabilities

Modular Python implementation:

- `config.py` — configuration and constants
- `ingestion.py` — data loading and schema validation
- `schema_validation.py` — column and type validation
- `normalization.py` — text, numeric, and code normalization
- `data_quality.py` — DQ checks and reporting
- `master_mapping.py` — reference master lookup
- `matching.py` — matching engine
- `reconciliation.py` — reconciliation classification
- `exposure.py` — financial exposure calculation
- `anomaly_detection.py` — analytical anomaly rules
- `kpis.py` — KPI computation
- `review_queue.py` — exception queue generation
- `reporting.py` — output formatting
- `utils.py` — shared utilities

See `src/` directory.

---

## Testing Strategy

Automated tests cover:

- Exact primary-ID matching
- Barcode and product-code matching
- Normalized and fuzzy name matching
- Equivalent product and substitute classification
- Missing source scenarios (A and B)
- Additional transaction and item scenarios
- Quantity, price, and amount variance handling
- Credit and reversal handling
- Duplicate-key handling
- Missing master records
- Invalid numeric handling
- Exposure calculation accuracy
- Confidence threshold behavior
- Manual-review logic
- Deterministic synthetic data generation
- Tolerance boundaries
- Anomaly severity classification
- Regression cases

Run tests: `pytest tests/`

---

## Power BI Design

Power BI-ready documentation (no PBIX file included):

- Star schema design
- Dimension and fact table definitions
- Relationship mapping
- DAX measure definitions
- Power Query transformation plan
- Dashboard layout
- Validation plan

See `docs/powerbi/` directory.

---

## Privacy & Synthetic Data Statement

**This project uses fully synthetic data created specifically for portfolio demonstration purposes.**

- No real customer, employee, transaction, prescription, company, or proprietary business data is included
- All names, identifiers, codes, amounts, and dates are fictional
- The synthetic data generator uses a fixed random seed for full reproducibility
- No real company logos, branding, or internal system names are used
- Generic terminology is used throughout (Source System A, Source System B, POS System, Reference Master)

See `PRIVACY_CHECKLIST.md` for the full privacy validation checklist.

---

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd transaction-reconciliation-anomaly-detection-analytics-portfolio

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

---

## Usage

```bash
# Generate synthetic data
python src/generate_data.py

# Run reconciliation pipeline
python src/main.py

# Run tests
pytest tests/ -v

# Open dashboard
open dashboard/index.html
```

---

## Repository Structure

```
├── README.md
├── LICENSE
├── .gitignore
├── .gitattributes
├── requirements.txt
├── CHANGELOG.md
├── CONTRIBUTING.md
├── SECURITY.md
├── PORTFOLIO_NOTES.md
├── PRIVACY_CHECKLIST.md
├── src/                    # Python analytical engine
├── tests/                  # Automated test suite
├── sql/                    # SQL analytical queries
├── data/
│   └── sample/             # Synthetic sample data
├── docs/                   # Documentation
│   ├── ARCHITECTURE.md
│   ├── DATA_DICTIONARY.md
│   ├── KPI_DICTIONARY.md
│   ├── MATCHING_METHODOLOGY.md
│   ├── RECONCILIATION_RULES.md
│   ├── EXPOSURE_METHODOLOGY.md
│   ├── ANOMALY_DETECTION.md
│   ├── DATA_QUALITY.md
│   ├── TEST_CASES.md
│   ├── BUSINESS_REQUIREMENTS.md
│   └── powerbi/
├── dashboard/              # HTML analytical dashboard
└── outputs/
    └── examples/           # Example output files
```

---

## Limitations

- Synthetic data does not capture all real-world edge cases
- Fuzzy matching thresholds are tuned for demonstration data; real deployments require calibration
- SQL scripts use portable syntax but may require dialect-specific adjustments
- Dashboard uses static synthetic data; production dashboards would connect to live data sources
- Anomaly detection rules are heuristic; real deployments require statistical validation

---

## Future Enhancements

- Multi-source reconciliation (3+ source systems)
- Time-series anomaly detection with statistical models
- Machine learning-based match confidence scoring
- Interactive dashboard with filtering and drill-down
- Automated report generation (PDF / Excel)
- CI/CD pipeline with automated testing
- Power BI .pbix implementation
- API layer for integration with external systems

---

## Skills Demonstrated

- Data reconciliation and matching algorithms
- Data quality engineering
- Anomaly detection
- Financial exposure analysis
- SQL analytics
- Python (pandas, numpy, rapidfuzz, pytest)
- HTML / CSS / JavaScript dashboard
- Power BI data modeling and DAX
- Automated testing
- Technical documentation
- Privacy-by-design
- Git / GitHub engineering discipline

---

## License

MIT License. See `LICENSE` file.

---

*Built as a portfolio demonstration project. All data is synthetic.*
