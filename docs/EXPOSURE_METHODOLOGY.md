# Exposure Methodology

## Overview

The exposure module (`src/exposure.py`) quantifies the financial impact of reconciliation discrepancies. Every reconciliation result is annotated with multiple exposure dimensions that decompose the total discrepancy into quantity, price, and amount components, plus unresolved and review-specific exposure.

Exposure is **never** labeled as fraud, loss, or theft. The terminology used throughout is: *exception exposure*, *unreconciled exposure*, *review exposure*, and *potential financial discrepancy*. These are neutral, analytical terms that describe the magnitude of discrepancy without assigning cause.

---

## Core Exposure Metrics

### Signed Exposure

```
signed_exposure = source_a_amount − source_b_amount
```

- **Positive** value → Source A recorded a higher amount than Source B
- **Negative** value → Source B recorded a higher amount than Source A
- **Zero** → Amounts agree within tolerance

Signed exposure preserves the direction of the discrepancy, which is essential for net exposure calculations and for understanding whether discrepancies systematically favor one source over the other.

---

### Absolute Exposure

```
absolute_exposure = |signed_exposure| = |source_a_amount − source_b_amount|
```

Absolute exposure represents the gross magnitude of the discrepancy regardless of direction. It is used for aggregation (total exposure across all lines) and for prioritization (larger discrepancies deserve more attention).

---

## Decomposed Exposure

The total discrepancy between Source A and Source B amounts can be decomposed into three contributing factors: quantity differences, price differences, and residual (amount) differences.

### Quantity Exposure

```
quantity_exposure = |quantity_difference × source_b_unit_price|
```

Quantifies the financial impact of the quantity difference, valued at Source B's unit price. Source B's price is used as the reference because it typically represents the authoritative billing amount.

**Example:**
```
Source A: qty = 8, unit_price = 10.00, amount = 80.00
Source B: qty = 10, unit_price = 10.00, amount = 100.00
quantity_difference = 8 − 10 = −2
quantity_exposure = |−2 × 10.00| = 20.00
```

---

### Price Exposure

```
price_exposure = |price_difference × source_a_quantity|
```

Quantifies the financial impact of the unit price difference, applied to Source A's quantity. Source A's quantity is used because it represents the volume at which the price variance applies from the POS perspective.

**Example:**
```
Source A: qty = 10, unit_price = 12.50, amount = 125.00
Source B: qty = 10, unit_price = 10.00, amount = 100.00
price_difference = 12.50 − 10.00 = 2.50
price_exposure = |2.50 × 10| = 25.00
```

---

### Amount Exposure (Residual)

```
amount_exposure = max(absolute_exposure − quantity_exposure − price_exposure, 0)
```

The residual after accounting for quantity and price differences. A non-zero amount exposure indicates that the amount discrepancy cannot be fully explained by the quantity and price differences alone — it may result from rounding, discounts, or computational differences in the source systems.

The `max(..., 0)` clamp handles floating-point arithmetic edge cases where the decomposition slightly over-accounts for the total.

---

## Special Exposure Categories

### Unresolved Exposure

```
IF reconciliation_status == "UNRESOLVED":
    unresolved_exposure = source_a_amount

IF reconciliation_status == "MISSING_IN_SOURCE_A":
    unresolved_exposure = source_b_amount  (the amount without a Source A counterpart)

IF reconciliation_status == "MISSING_IN_SOURCE_B":
    unresolved_exposure = source_a_amount  (the amount without a Source B counterpart)

OTHERWISE:
    unresolved_exposure = 0.0
```

Unresolved exposure represents the full amount at risk for lines where reconciliation could not establish a match. The full amount is used (not the difference) because with no counterpart, the entire transaction amount is potentially discrepant.

**Why different sources for different missing statuses:**
- `MISSING_IN_SOURCE_A` → Use Source B amount (the only available amount)
- `MISSING_IN_SOURCE_B` → Use Source A amount (the only available amount)
- `UNRESOLVED` → Use Source A amount (the POS side, as the primary transaction source)

---

### Review Exposure

```
IF review_required == "Y":
    review_exposure = absolute_exposure
OTHERWISE:
    review_exposure = 0.0
```

Review exposure captures the total absolute discrepancy that requires manual analyst attention. It sums the absolute exposure across all lines flagged for review, providing a measure of the financial scope of the review workload.

---

## Exposure Aggregation

### By Reconciliation Status

The `exposure_summary()` function aggregates exposure metrics by reconciliation status:

| Output Column | Aggregation |
|---|---|
| `count` | Number of lines per status |
| `total_signed_exposure` | `SUM(signed_exposure)` |
| `total_absolute_exposure` | `SUM(absolute_exposure)` |
| `total_unresolved_exposure` | `SUM(unresolved_exposure)` |
| `total_review_exposure` | `SUM(review_exposure)` |

---

## Exposure Accounting Identity

For any individual line, the following identity holds:

```
absolute_exposure = quantity_exposure + price_exposure + amount_exposure
                   (with floating-point tolerance)
```

The `amount_exposure` is defined as the residual, so the decomposition always balances. If the quantity and price exposures happen to exceed the absolute exposure (due to floating-point arithmetic or compounding effects), the residual is clamped to zero.

---

## Handling of Missing Data

| Scenario | signed_exposure | absolute_exposure | qty/price/amount_exposure |
|---|---|---|---|
| Source A amount missing | `0 − source_b_amount` | `source_b_amount` | 0 (no Source A side to decompose) |
| Source B amount missing | `source_a_amount − 0` | `source_a_amount` | 0 (no Source B side to decompose) |
| Both amounts missing | 0 | 0 | 0 |

Missing amounts are treated as 0.0 for exposure computation. The `unresolved_exposure` field captures the full amount for truly missing counterparts.

---

## Language Standards

| ✅ Use | ❌ Avoid |
|---|---|
| Exception exposure | Fraud exposure |
| Unreconciled exposure | Loss exposure |
| Review exposure | Theft exposure |
| Potential financial discrepancy | Suspected fraud |
| Discrepancy | Irregularity (implies wrongdoing) |
| Unmatched amount | Missing money |
| Variance | Deficit/surplus (directional bias) |

All exposure metrics are neutral, quantitative measures of discrepancy magnitude. They do not imply cause, intent, or outcome.
