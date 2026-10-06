# Transaction Reconciliation & Exception Intelligence

## Explainable Multi-Source Matching, Exposure Analysis & Review Prioritization

This repository implements a deterministic transaction-reconciliation engine for comparing two synthetic source systems, resolving records through an **8-level explainable matching hierarchy**, deriving component-level reconciliation statuses, quantifying exception exposure, detecting rule-based anomalies and routing review items by priority.

> **Data boundary:** every product, branch, employee, transaction, identifier, amount and scenario is synthetic. The project does not contain real customer, employee, company, transaction or proprietary business data. Exception exposure is not labeled as fraud or confirmed loss.

<img src="docs/assets/Transaction%20Reconciliation%20Analytics%20Dashboard.png" alt="Transaction Reconciliation and Anomaly Detection Analytics overview" width="100%">

> **Visual evidence note:** the infographic is a presentation schematic. Exact match-method names, thresholds and KPI percentages are governed by the source code and retained runtime outputs documented below.

**Start here:** [Case study](docs/CASE_STUDY.md) · [Technical walkthrough](docs/TECHNICAL_WALKTHROUGH.md) · [Evidence map](docs/PROJECT_EVIDENCE_MAP.md) · [Project index](docs/PROJECT_INDEX.md) · [Final validation](docs/FINAL_RELEASE_VALIDATION.md)

## Project at a glance

| Area | Current implementation |
|---|---|
| Sources | Synthetic Source A + Source B transaction systems |
| Deterministic seed | `20260902` |
| Reference entities | 150 products · 10 branches · 32 employees |
| Controlled scenarios | 28 scenario types with retained expected ground truth |
| Matching | 8 ordered methods with explicit method + confidence |
| Reconciliation | Identity · Quantity · Price · Amount components |
| Status framework | 17 governed reconciliation statuses |
| Anomaly layer | 7 deterministic business-rule detectors |
| Review routing | CRITICAL / HIGH / MEDIUM / LOW priority |
| Current example output | 2,424 reconciliation lines |
| Implemented presentation | Interactive HTML/Chart.js analytical dashboard |
| Additional analytics | 12 SQL analytical scripts |
| BI extension | Power BI model/DAX/Power Query/validation **design blueprint**, not a committed PBIP/PBIR runtime implementation |
| Validation | pytest + deterministic generation manifest + scenario ground truth + repository CI |

## Why this project exists

Cross-system reconciliation becomes difficult when identifiers are inconsistent, descriptions vary, quantities or prices differ, transactions are missing, master data is incomplete or a match is possible but uncertain.

The project separates those concerns instead of hiding them behind one opaque score:

```text
Synthetic Source A + Source B
        ↓
Ingestion & Normalization
        ↓
Schema + Data Quality Validation
        ↓
Master / Reference Mapping
        ↓
8-Level Explainable Matching
        ↓
4-Component Reconciliation
Identity → Quantity → Price → Amount
        ↓
Financial Exposure Decomposition
        ↓
Rule-Based Anomaly Detection
        ↓
Prioritized Review Queue
        ↓
KPIs + SQL + HTML Decision Support
```

## Explainable matching hierarchy

The matcher follows an ordered, auditable hierarchy:

1. `EXACT_PRIMARY_ID` — confidence 100
2. `EXACT_BARCODE` — 97
3. `EXACT_PRODUCT_CODE` — 95
4. `NORMALIZED_NAME` — 90
5. `FUZZY_NAME` — score-based acceptance
6. `GENERIC_STRENGTH_EQUIVALENT` — 85
7. `POSSIBLE_SUBSTITUTE` — 70
8. `UNMATCHED` — 0

Each result retains the method and confidence used. Matching is therefore reviewable and explainable rather than a black-box classification.

See [Matching Methodology](docs/MATCHING_METHODOLOGY.md).

## Reconciliation model

Matching identity is only the first step. Reconciliation separately evaluates:

- **Identity**
- **Quantity**
- **Price**
- **Amount**

The overall status is derived from those components using governed tolerances:

- Unit price: ±0.01
- Amount: ±0.02
- Quantity: ±0.0001

The current configuration defines **17 reconciliation statuses**, including clean matches, substitutes, missing-source cases, quantity/price/amount differences, credits, reversals, duplicate/data-quality exceptions and unresolved items.

See [Reconciliation Rules](docs/RECONCILIATION_RULES.md).

## Financial exposure

Exposure is decomposed rather than represented as one ambiguous number. The pipeline calculates:

- signed exposure;
- absolute exposure;
- quantity exposure;
- price exposure;
- amount exposure;
- unresolved exposure;
- review exposure.

These are **analytical discrepancy measures**. They do not prove fraud, misconduct or realized financial loss.

See [Exposure Methodology](docs/EXPOSURE_METHODOLOGY.md).

## Anomaly detection

The implemented anomaly layer contains seven deterministic rule families:

- high-value outlier;
- low-confidence match;
- data-quality exception;
- missing master data;
- duplicate key;
- unresolved transaction;
- missing counterpart.

Each emitted anomaly retains a type, severity, description and reconciliation status.

The current committed example output contains four anomaly types because not every detector is necessarily triggered by the current generated run.

See [Anomaly Detection](docs/ANOMALY_DETECTION.md).

## Review queue

Only rows marked for review are routed into the investigation queue. Priority is derived from reconciliation status, exposure and attached anomaly severity.

A hardening fix in the current release ensures that a **CRITICAL anomaly severity actually escalates the review priority to CRITICAL**. The prior implementation stored anomaly types but compared them to a severity label, so that escalation path could not fire. A dedicated regression test now covers this behavior.

### Review-queue grain

`line_key` is the operational reconciliation-line reference, not a guaranteed globally unique case identifier. Controlled duplicate scenarios can intentionally produce repeated line keys. A future operationalization step should introduce a dedicated immutable `review_item_id` if case-level workflow persistence is required.

## Current synthetic evidence

The committed example output reports:

| Metric | Value |
|---|---:|
| Reconciliation lines | 2,424 |
| Matched lines | 1,170 |
| Exception lines | 1,174 |
| Match rate | 48.27% |
| Exception rate | 48.43% |
| Review-required lines | 1,182 |
| Review rate | 48.76% |
| Average confidence | 89.20 |
| Total absolute exposure | 818,612.86 |
| Unresolved exposure | 256,344.73 |

The high exception/review rates are **not a benchmark for real transaction operations**. The synthetic dataset is intentionally scenario-heavy so the engine can exercise matching, discrepancy, anomaly, data-quality and missing-record paths.

## Deterministic synthetic data

The generator uses fixed seed `20260902` and commits a SHA-256 manifest for the generated sample.

Current manifest evidence:

- 150 products;
- 10 branches;
- 32 employees;
- 2,305 Source A headers;
- 2,385 Source A lines;
- 2,095 Source B headers;
- 2,095 Source B lines;
- 2,260 expected scenario records.

The test suite now regenerates the sample and compares the generated file metadata and SHA-256 hashes with the committed manifest.

## Implemented dashboard

The repository contains a real interactive HTML dashboard:

`dashboard/reconciliation_dashboard.html`

It consumes the generated analytical outputs and uses Chart.js for KPI, distribution, trend and investigation views.

This HTML implementation is the current executable visualization layer stored in the repository.

## SQL analytical layer

The `sql/` directory contains 12 analytical scripts covering reconciliation status, matching, exposure, branches, employees, data quality, anomaly distribution, review queue, scenario ground truth, category reconciliation, duplicate detection and fuzzy-match review candidates.

SQL is an analysis layer over the generated outputs; the Python pipeline remains the authoritative implementation of matching and reconciliation logic.

## Power BI boundary

`docs/powerbi/` contains a detailed **design blueprint** for a possible Power BI implementation:

- model design;
- Power Query plan;
- DAX measure definitions;
- dashboard design;
- validation plan.

There is currently **no committed PBIP/PBIR/TMDL or PBIX implementation** in this repository. The Power BI documents must therefore be read as design specifications and validation plans, not as runtime evidence.

See [Power BI Blueprint Boundary](docs/powerbi/README.md).

## Validation strategy

Validation is layered:

| Layer | Evidence |
|---|---|
| Generator determinism | Byte-identical generation tests |
| Committed sample reproducibility | Generated manifest reconciled to committed SHA-256 manifest |
| Configuration | Match hierarchy, status sets, scenario catalog and tolerances tested |
| Matching | Hierarchy, confidence and one-result-per-Source-A-line tests |
| Reconciliation | Component status, exposure, anomaly and KPI tests |
| Review queue | Priority ordering + CRITICAL severity escalation regression |
| Ground truth | Controlled scenario coverage and regression checks |
| End-to-end | Pipeline generates reconciliation, DQ, anomaly, review, KPI and dashboard artifacts |
| CI | GitHub Actions executes static repository checks + full pytest suite |

## Quick Start

```bash
git clone https://github.com/khaledzidan203-stack/transaction-reconciliation-anomaly-detection-analytics.git
cd transaction-reconciliation-anomaly-detection-analytics

python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt

python -c "from src.synthetic_data_generator import generate_all; generate_all()"
python -c "from src.pipeline import run_pipeline; run_pipeline()"
pytest -q
```

Open `dashboard/reconciliation_dashboard.html` after generating the outputs.

## Repository structure

```text
src/                  Python analytical engine
tests/                automated unit/integration/regression tests
data/sample/          deterministic synthetic source data + manifest
outputs/examples/     retained example analytical outputs
sql/                  12 analytical SQL scripts
dashboard/            implemented HTML/Chart.js dashboard
docs/                 methodology, contracts and validation
docs/powerbi/         Power BI design blueprint only
docs/assets/          presentation assets
.github/workflows/    repository quality gate
```

## Documentation

- [Project Index](docs/PROJECT_INDEX.md)
- [Case Study](docs/CASE_STUDY.md)
- [Technical Walkthrough](docs/TECHNICAL_WALKTHROUGH.md)
- [Project Evidence Map](docs/PROJECT_EVIDENCE_MAP.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Data Dictionary](docs/DATA_DICTIONARY.md)
- [Matching Methodology](docs/MATCHING_METHODOLOGY.md)
- [Reconciliation Rules](docs/RECONCILIATION_RULES.md)
- [Exposure Methodology](docs/EXPOSURE_METHODOLOGY.md)
- [Anomaly Detection](docs/ANOMALY_DETECTION.md)
- [Data Quality](docs/DATA_QUALITY.md)
- [KPI Dictionary](docs/KPI_DICTIONARY.md)
- [Final Release Validation](docs/FINAL_RELEASE_VALIDATION.md)

## Limitations

- All data is synthetic and deliberately scenario-heavy.
- Rule-based anomalies are review signals, not fraud determinations.
- Exposure measures are analytical discrepancies, not confirmed losses.
- Fuzzy matching remains threshold-dependent.
- `line_key` is not a durable case-management identifier.
- Power BI is documented as a blueprint only; the implemented visualization artifact is the HTML dashboard.
- The project models reconciliation logic, not a transactional production service or human investigation workflow.

Licensed under the [MIT License](LICENSE).
