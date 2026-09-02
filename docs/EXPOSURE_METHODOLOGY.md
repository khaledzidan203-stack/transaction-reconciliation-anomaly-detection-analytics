# Exposure Methodology

> Full exposure methodology documentation will be added in Phase 8.

## Exposure Metrics

| Metric | Formula |
|---|---|
| Signed Exposure | Source A amount − Source B amount |
| Absolute Exposure | \|Signed Exposure\| |
| Positive Exposure | MAX(Signed Exposure, 0) |
| Negative Exposure | MIN(Signed Exposure, 0) |
| Quantity Exposure | Source A qty − Source B qty |
| Price Exposure | Source A unit price − Source B unit price |
| Amount Exposure | Source A amount − Source B amount |
| Total Exception Exposure | SUM(\|Amount Exposure\|) for all exceptions |
| Unresolved Exposure | SUM(\|Amount Exposure\|) for UNRESOLVED cases |
| Review Exposure | SUM(\|Amount Exposure\|) for review-required cases |

## Language

Exposure is never automatically labeled as fraud or loss.

Use: *exception exposure*, *unreconciled exposure*, *review exposure*, *potential financial discrepancy*.
