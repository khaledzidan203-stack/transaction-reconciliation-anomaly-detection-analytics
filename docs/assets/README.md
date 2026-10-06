# Presentation Assets

This directory contains presentation-only visual assets for the Transaction Reconciliation & Exception Intelligence project.

## Current overview

`Transaction Reconciliation Analytics Dashboard.png`

The root README uses this image as a visual summary of the end-to-end architecture.

The graphic should be read as a presentation schematic. Exact method names, thresholds, statuses and runtime values are governed by the repository source and evidence files.

## Evidence-supported facts

The repository supports the following high-level claims:

- deterministic synthetic generation with seed `20260902`;
- Source A + Source B reconciliation;
- normalization, schema validation and data-quality checks;
- 8-level explainable matching;
- identity, quantity, price and amount reconciliation components;
- 17 reconciliation statuses;
- financial exposure decomposition;
- 7 anomaly rule families;
- prioritized review queue;
- 28 controlled scenario types;
- current retained example output of 2,424 reconciliation lines;
- implemented HTML/Chart.js dashboard;
- SQL analytical scripts.

## Evidence boundary

Presentation assets are not source data, runtime reconciliation evidence, SQL execution evidence or Power BI runtime evidence.

Authoritative claims remain defined by the Python source, tests, generation manifest, retained outputs, SQL scripts, HTML dashboard and project documentation.
