# Project Notes

## Purpose

This repository demonstrates a governed, explainable transaction-reconciliation and exception-intelligence workflow using deterministic synthetic data.

## Key design choices

1. **Generic domain** — fictional products, branches, employees and systems keep the implementation independent from any real employer or operating environment.
2. **Privacy by design** — no real customer, employee, transaction, company or proprietary identifiers are included.
3. **Deterministic reproducibility** — `RANDOM_SEED = 20260902` and SHA-256 manifests make the synthetic sample reproducible.
4. **Controlled scenarios** — 28 injected scenario types provide known ground truth for matching, reconciliation and exception paths.
5. **Explainable matching** — every match retains method and confidence.
6. **Component reconciliation** — identity, quantity, price and amount are evaluated separately before the overall status is derived.
7. **Conservative terminology** — anomaly flags and exposure values are review signals, not allegations of fraud or confirmed loss.

## Implemented analytical layers

- Python reconciliation engine
- deterministic synthetic generator
- automated pytest suite
- SQL analytical scripts
- HTML/Chart.js dashboard
- retained example outputs
- Power BI design blueprint

## Current implementation boundary

The HTML dashboard is implemented and committed.

The Power BI material under `docs/powerbi/` is a design blueprint only; no PBIP/PBIR/TMDL runtime implementation is claimed.

## Known operationalization boundary

`line_key` is suitable for analytical traceability but controlled duplicate scenarios can repeat it. A persistent case-management workflow should introduce a dedicated immutable review-item identifier.
