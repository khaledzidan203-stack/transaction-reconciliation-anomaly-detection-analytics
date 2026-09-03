# Portfolio Notes

## Purpose

This project is a **portfolio demonstration** of end-to-end transaction
reconciliation and anomaly detection analytics.

## Key Design Choices

1. **Generic retail/distribution domain** — The project deliberately uses a
   generic retail domain with fictional brand names (ZENITH, AURORA, NEXUS,
   etc.) to create a clean separation from any specific industry or employer.

2. **Privacy-by-design** — No real company names, employee names, proprietary
   identifiers, or business logic from any employer appear anywhere in this
   repository. All data is synthetically generated with a fixed random seed.

3. **Deterministic reproducibility** — Every data file, pipeline output and
   test result is fully reproducible via `RANDOM_SEED = 20260902`. Running
   the generator twice produces byte-identical CSV files.

4. **28 controlled injection scenarios** — The synthetic data includes
   deliberately injected reconciliation scenarios (clean matches, missing
   transactions, quantity/price variances, fuzzy matches, data quality
   failures, etc.) with known ground truth for validation.

5. **Explainable matching** — Every matched pair includes the match method
   used and a confidence score, enabling full audit trails and review
   prioritization.

6. **Component status architecture** — Reconciliation statuses are derived
   from independent identity/quantity/price/amount component statuses,
   providing granular discrepancy analysis.

## What This Project Demonstrates

### Analytical Thinking
- Multi-source reconciliation logic
- Explainable matching with transparent decision trails
- Financial exposure quantification
- Anomaly detection with severity classification
- Exception management and review queue generation

### Technical Skills
- **Python** — pandas, numpy, rapidfuzz, pytest
- **SQL** — schema design, analytical queries, validation
- **HTML/CSS/JS** — analytical dashboard with charts
- **Power BI** — star schema, DAX, Power Query documentation
- **Testing** — comprehensive automated test suite
- **Git** — clean commit history, documentation

## What This Project Does NOT Claim

- No real fraud was detected
- No real company losses were identified
- No real transactions were analyzed
- No real employees were investigated

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.13 |
| Data | pandas 3.0, numpy |
| Fuzzy matching | rapidfuzz |
| Testing | pytest |
| Visualization | Chart.js (HTML dashboard) |
| BI documentation | Power BI (model design only) |
| SQL | ANSI SQL (analytical scripts) |

## How to Use This in a Portfolio

1. Link to this repository in your resume or LinkedIn
2. Highlight specific components relevant to the role:
   - Data Analyst → KPIs, dashboard, SQL
   - Fraud Analyst → anomaly detection, exposure analysis
   - BI Analyst → Power BI documentation, star schema
   - Analytics Engineer → Python pipeline, testing, architecture
3. Be prepared to discuss:
   - Matching methodology and thresholds
   - Exposure calculation formulas
   - Anomaly detection rules
   - Data quality approach
   - Testing strategy
