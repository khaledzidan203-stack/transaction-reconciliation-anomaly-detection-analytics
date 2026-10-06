# Final Release Validation

## Release scope

This release hardens the repository without changing the validated matching hierarchy, reconciliation rules, exposure formulas or synthetic scenario design.

## Technical changes

- corrected CRITICAL anomaly severity escalation in the review queue;
- added regression coverage for that path;
- added committed-sample reproducibility validation against the generation manifest;
- removed unused anomaly-threshold imports;
- added repository CI;
- rebuilt public documentation around evidence-backed claims;
- separated implemented HTML reporting from Power BI design-only documentation.

## Current runtime evidence

Retained example KPI output:

- total reconciliation lines: 2,424;
- matched lines: 1,170;
- exception lines: 1,174;
- review-required lines: 1,182;
- average confidence: 89.20;
- total absolute exposure: 818,612.86;
- unresolved exposure: 256,344.73.

## Validation boundary

Fresh GitHub Actions validation covers:

- repository contract;
- protected core artifacts;
- Python source compilation;
- deterministic synthetic generation tests;
- committed manifest reconciliation;
- unit/integration/regression pytest suite.

SQL scripts are static analytical queries and are not executed by GitHub Actions.

The HTML dashboard is an implemented repository artifact, but browser screenshot regression is not part of CI.

Power BI documents are a blueprint only. No fresh Power BI Desktop, PBIP/PBIR/TMDL or DAX runtime validation is claimed.

## Known limitation

`line_key` can repeat in controlled duplicate scenarios and is not a persistent case-management identifier. A production workflow should introduce an immutable review-item key if queue state must survive across refreshes.

## Safety rule

Exception exposure and anomaly flags are investigation signals. They are not proof of fraud, misconduct or realized financial loss.
