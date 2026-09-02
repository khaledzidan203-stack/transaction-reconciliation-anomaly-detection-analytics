# Data Quality

> Full data quality documentation will be added in Phase 8.

## DQ Categories

| Category | Description |
|---|---|
| ERROR | Critical issue preventing processing |
| WARNING | Notable issue, processing continues |
| BUSINESS_ANOMALY | Unusual but valid pattern |

## Validations

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

## DQ Report

Each DQ issue records:
- Source system
- Issue type
- Affected row / record
- Severity
- Description
- Recommended action
