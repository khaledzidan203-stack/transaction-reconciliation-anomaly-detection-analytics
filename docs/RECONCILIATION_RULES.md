# Reconciliation Rules

> Full reconciliation rules documentation will be added in Phase 8.

## Reconciliation Statuses

| Status | Description |
|---|---|
| MATCHED | Exact or high-confidence match |
| MATCHED_WITH_SUBSTITUTE | Equivalent product matched |
| MISSING_IN_SOURCE_A | Item exists in Source B only |
| MISSING_IN_SOURCE_B | Item exists in Source A only |
| ADDITIONAL_TRANSACTION | Entire transaction exists in one source only |
| ADDITIONAL_ITEM | Individual line item exists in one source only |
| QUANTITY_DIFFERENCE | Matched item with quantity variance |
| PRICE_DIFFERENCE | Matched item with price variance |
| AMOUNT_DIFFERENCE | Matched item with amount variance |
| QUANTITY_AND_AMOUNT_DIFFERENCE | Combined variance |
| CREDIT | Credit-only transaction |
| REVERSAL | Reversal transaction |
| FUZZY_MATCH_REVIEW | Low-confidence match requiring analyst review |
| MASTER_DATA_EXCEPTION | Missing or invalid master data |
| DUPLICATE_KEY | Duplicate transaction detected |
| DATA_QUALITY_EXCEPTION | Data quality issue prevents matching |
| UNRESOLVED | No classification possible |

## Decision Logic

*To be documented with decision trees.*
