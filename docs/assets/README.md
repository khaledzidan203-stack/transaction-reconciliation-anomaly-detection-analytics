# Presentation Assets

This directory contains presentation-only visual assets for the Transaction Reconciliation & Anomaly Detection Analytics project.

## Intended use

The primary overview image stored here is used by the repository README to explain the end-to-end analytical workflow at a glance.

Recommended filename:

`transaction_reconciliation_anomaly_detection_overview.png`

The overview should represent only repository-supported claims, including:

- fully synthetic, deterministic data generated with seed `20260902`;
- two transaction source systems plus governed master/reference data;
- normalization, schema validation and data-quality controls;
- an 8-level explainable hierarchical matching engine;
- four reconciliation components: identity, quantity, price and amount;
- 17 reconciliation statuses;
- financial exposure decomposition;
- 7 rule-based anomaly detectors;
- a prioritized manual-review queue;
- KPI, SQL and HTML dashboard outputs;
- 28 controlled scenario types with retained ground truth;
- current example output of 2,424 reconciliation lines.

## Evidence boundary

Assets in this directory are presentation summaries only. They are not source data, reconciliation evidence, runtime test output, SQL evidence, or Power BI runtime evidence.

Authoritative claims remain defined by the Python source, tests, synthetic generation manifest, example outputs, SQL scripts, HTML dashboard, and project documentation.
