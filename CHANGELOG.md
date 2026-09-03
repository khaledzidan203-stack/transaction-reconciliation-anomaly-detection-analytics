# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-09-02

### Added
- Central configuration module (`src/config.py`) with all constants, tolerances, statuses, and 28 scenario definitions
- Deterministic IO utilities (`src/utils.py`) with SHA-256 hashing and CSV/JSON round-trips
- Comprehensive normalization framework (`src/normalization.py`) including Unicode NFKC, EAN-13 validation, unit-split canonicalization, and numeric parsing
- Deterministic synthetic data generator (`src/synthetic_data_generator.py`) with fixed seed 20260902, producing 150 products, 10 branches, 32 employees, 2K+ transactions, and 28 controlled injection scenarios with ground truth
- Data ingestion module (`src/ingestion.py`) with normalized key columns
- Schema validation module (`src/schema_validation.py`) for column structure checks
- Data quality engine (`src/data_quality.py`) detecting duplicates, malformed identifiers, invalid numerics, and missing master references
- Master data mapping (`src/master_mapping.py`) with product/branch/employee lookup dictionaries
- Explainable matching engine (`src/matching.py`) implementing 8-level hierarchical matcher with inverted token index
- Reconciliation engine (`src/reconciliation.py`) computing component statuses (identity/quantity/price/amount) and overall reconciliation status
- Exposure analysis (`src/exposure.py`) quantifying signed, absolute, quantity, price, amount, unresolved, and review exposure
- Anomaly detection (`src/anomaly_detection.py`) with 7 rule-based detection rules across 4 severity levels
- KPI framework (`src/kpis.py`) computing summary, by-branch, and by-month metrics
- Review queue (`src/review_queue.py`) with CRITICAL/HIGH/MEDIUM/LOW prioritization
- Reporting module (`src/reporting.py`) writing all output CSVs and dashboard JSON
- Pipeline orchestrator (`src/pipeline.py`) running the full end-to-end workflow
- Comprehensive test suite: 122 tests across 8 test modules, 0 failures
- 12 SQL analytical scripts covering reconciliation, exposure, anomalies, and ground-truth validation
- Interactive HTML analytics dashboard with Chart.js visualizations
- Power BI model documentation (5 files)
- Complete project documentation (11 files)
