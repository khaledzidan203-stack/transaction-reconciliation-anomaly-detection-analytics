# Case Study — Transaction Reconciliation & Exception Intelligence

## Context

Two transaction systems can describe the same commercial event differently. Product identifiers may disagree, descriptions may be formatted differently, quantities and prices can vary, counterpart records can be missing, and some records should be reviewed even when a match is technically possible.

This project implements a deterministic synthetic reconciliation platform that keeps those decisions explicit and reviewable.

## Analytical challenge

A useful reconciliation process has to answer several separate questions:

1. Are the two records referring to the same item?
2. How confident is the identity match?
3. Do quantity, price and amount agree within governed tolerances?
4. If they do not agree, what type of discrepancy exists?
5. What analytical exposure is associated with the discrepancy?
6. Does the line trigger an anomaly rule?
7. Does the item require review, and with what priority?

A single opaque “match / no-match” flag is not sufficient.

## Solution architecture

The implemented flow is:

```text
Deterministic Synthetic Sources
→ Ingestion & Normalization
→ Schema + Data Quality Checks
→ Master Mapping
→ 8-Level Matching
→ 4-Component Reconciliation
→ Exposure Decomposition
→ 7-Rule Anomaly Detection
→ Prioritized Review Queue
→ KPI / SQL / HTML Analytics
```

## Explainability by design

The match engine uses a fixed ordered hierarchy from exact identifiers through normalized and fuzzy text to substitutes and unmatched cases. Every reconciliation result retains:

- match method;
- confidence score;
- identity status;
- quantity status;
- price status;
- amount status;
- final reconciliation status;
- review flag.

This gives an analyst a transparent decision trail instead of a black-box label.

## Controlled test data

The generator uses seed `20260902` and 28 scenario types. The committed sample includes:

- 150 synthetic products;
- 10 branches;
- 32 employees;
- 2,305 Source A headers;
- 2,385 Source A lines;
- 2,095 Source B headers;
- 2,095 Source B lines;
- 2,260 expected scenario records.

The generated files are fingerprinted in a SHA-256 manifest.

## Current example outcome

The retained example run produces 2,424 reconciliation lines:

- 1,170 matched lines;
- 1,174 exception lines;
- 1,182 review-required lines;
- average confidence 89.20;
- total absolute exposure 818,612.86;
- unresolved exposure 256,344.73.

These rates are not operational benchmarks. The synthetic data intentionally injects many exception scenarios to exercise the engine.

## Hardening finding and fix

During repository review, one logic issue was identified in review prioritization.

The previous implementation stored anomaly **types** in the anomaly map but checked that list for the literal severity value `CRITICAL`. That meant a critical anomaly severity could not trigger the intended priority upgrade.

The code now tracks critical anomaly severity separately and a dedicated regression test verifies that a critical anomaly upgrades the queue item to `CRITICAL`.

This fix does not change the matching or reconciliation rules.

## Validation

The repository validates:

- deterministic generation;
- committed sample hashes;
- configuration and hierarchy contracts;
- normalization and DQ behavior;
- matching outputs and confidence;
- reconciliation components;
- exposure invariants;
- anomaly severities;
- KPI ranges;
- review ordering and severity escalation;
- controlled scenario coverage;
- end-to-end output creation.

GitHub Actions executes the repository validator and pytest suite on each push and pull request.

## Presentation layer

The implemented reporting artifact is an HTML/Chart.js dashboard.

Power BI documentation is retained as a design blueprint only. No PBIP/PBIR/TMDL implementation is claimed.

## Engineering outcome

The project demonstrates how reconciliation can be treated as a governed analytical workflow rather than a one-step comparison:

**explainable matching → component reconciliation → discrepancy exposure → anomaly signal → review priority → decision support.**
