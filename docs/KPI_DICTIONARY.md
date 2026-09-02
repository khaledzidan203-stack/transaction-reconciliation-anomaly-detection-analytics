# KPI Dictionary

> Full KPI dictionary will be added in Phase 8.

## KPIs

| Name | Definition | Formula |
|---|---|---|
| Total Transactions | Count of unique transactions | COUNT(DISTINCT transaction_id) |
| Total Transaction Lines | Count of transaction line items | COUNT(*) |
| Matched Lines | Lines with MATCHED status | COUNT WHERE status = 'MATCHED' |
| Match Rate | Percentage of lines matched | Matched Lines / Total Lines |
| Exact Match Rate | Percentage with exact match method | Exact Matches / Total Lines |
| Fuzzy Match Rate | Percentage with fuzzy match method | Fuzzy Matches / Total Lines |
| Unmatched Rate | Percentage unmatched | Unmatched / Total Lines |
| Exception Rate | Percentage with exceptions | Exceptions / Total Lines |
| Manual Review Rate | Percentage requiring review | Review Cases / Total Lines |
| Total Absolute Exposure | Sum of absolute exposure amounts | SUM(\|exposure\|) |
| Signed Net Exposure | Net signed exposure | SUM(exposure) |
| Unresolved Exposure | Exposure from unresolved cases | SUM(\|exposure\|) WHERE status = 'UNRESOLVED' |

## Format

Each KPI entry will include:
- Name
- Definition
- Formula
- Grain
- Numerator
- Denominator
- Filters
- Interpretation
