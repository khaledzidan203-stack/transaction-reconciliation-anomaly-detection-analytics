# Data Dictionary

> Full data dictionary will be added in Phase 8.

## Entities

| Entity | Grain | Description |
|---|---|---|
| `transaction_header` | One row per transaction per source system | Top-level transaction record |
| `transaction_line` | One row per transaction item per source system | Individual line item within a transaction |
| `product_master` | One row per synthetic product | Reference product catalog |
| `branch_master` | One row per synthetic branch | Reference branch catalog |
| `employee_master` | One row per synthetic employee | Reference employee catalog |
| `reconciliation_result` | One row per reconciled transaction-line comparison | Match result with status and evidence |
| `data_quality_issue` | One row per detected DQ issue | Data quality finding |
| `anomaly_result` | One row per detected analytical anomaly | Anomaly finding with severity |
| `review_queue` | One row per unresolved / exception case | Case requiring manual review |

## Column Definitions

*To be documented per entity.*
