# Anomaly Detection

> Full anomaly detection documentation will be added in Phase 8.

## Anomaly Rules

- Unusually high transaction amount
- Unusual quantity or unit price
- Repeated duplicate transactions
- Excessive manual-review rate by branch or employee
- Abnormal credit or reversal frequency
- Repeated quantity or price variance
- Unusually low match confidence
- Abnormal unmatched item count
- Abnormal transaction frequency
- Anomalous exposure concentration

## Severity Levels

| Level | Description |
|---|---|
| LOW | Minor deviation, informational |
| MEDIUM | Notable deviation, may require attention |
| HIGH | Significant deviation, requires investigation |
| CRITICAL | Extreme deviation, immediate attention required |

## Separation

Anomaly detection is separate from reconciliation status. A matched transaction can still have an anomaly (e.g., unusually high amount).
