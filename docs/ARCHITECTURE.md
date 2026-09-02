# Architecture

> Full architecture documentation will be added in Phase 8.

## Overview

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

## Components

- **Ingestion** — load source data, validate schema
- **Normalization** — standardize text, codes, numeric values
- **Data Quality** — detect issues before reconciliation
- **Master Mapping** — link source products to reference master
- **Matching** — deterministic and fuzzy matching hierarchy
- **Reconciliation** — classify match results into standard statuses
- **Exposure** — calculate financial discrepancy amounts
- **Anomaly Detection** — identify unusual patterns
- **Review Queue** — route exceptions for manual review
- **KPIs** — compute analytical metrics
- **Dashboard** — visualize results
- **SQL** — analytical queries
- **Documentation** — methodology, dictionaries, design

## Data Flow

Source systems provide transaction data → pipeline normalizes, validates, matches, reconciles → results feed KPIs, dashboard, and review queue.

## Design Principles

- Explainable — every decision is traceable
- Deterministic — reproducible with fixed seed
- Modular — each component is independent
- Testable — comprehensive automated tests
- Privacy-safe — synthetic data only
