# Reconciliation Rules

## Overview

The reconciliation engine (`src/reconciliation.py`) assigns an overall status to each matched line pair by independently computing four component statuses — **identity**, **quantity**, **price**, and **amount** — and then deriving the overall status from their combination.

This two-layer approach (component → overall) ensures that the reason for any discrepancy is always traceable to a specific dimension.

---

## Component Status Derivation

### Identity Status

The identity component reflects *what* was matched, not *how well* it matched numerically.

| Status | Condition | Match Methods |
|---|---|---|
| `IDENTITY_MATCHED` | Same product confirmed via a deterministic identifier | `EXACT_PRIMARY_ID`, `EXACT_BARCODE`, `EXACT_PRODUCT_CODE`, `NORMALIZED_NAME` |
| `IDENTITY_SUBSTITUTE` | Equivalent or similar product, different brand | `FUZZY_NAME`, `GENERIC_STRENGTH`, `POSSIBLE_SUBSTITUTE` |
| `IDENTITY_UNMATCHED` | No match found | `UNMATCHED` |
| `IDENTITY_MISSING_IN_SOURCE_A` | Only in Source B | Source A line_id is empty |
| `IDENTITY_MISSING_IN_SOURCE_B` | Only in Source A | Source B line_id is empty |

**Design note:** `FUZZY_NAME` is classified as `IDENTITY_SUBSTITUTE` because even with a high similarity score, a fuzzy match implies the product names are not identical — there is residual uncertainty about whether they are the same commercial product.

---

### Quantity Status

Compares Source A quantity against Source B quantity using a tolerance.

| Status | Condition |
|---|---|
| `QUANTITY_MATCHED` | `|qty_a − qty_b| ≤ QUANTITY_TOLERANCE` (0.0001) |
| `QUANTITY_SHORTAGE` | `qty_a < qty_b` and difference exceeds tolerance |
| `QUANTITY_EXCESS` | `qty_a > qty_b` and difference exceeds tolerance |
| `QUANTITY_NOT_APPLICABLE` | Either qty_a or qty_b is None (unparseable or missing) |

**Tolerance:** `QUANTITY_TOLERANCE = 0.0001` — extremely tight, effectively requiring exact quantity agreement. This is intentional for reconciliation precision.

---

### Price Status

Compares Source A unit price against Source B unit price using a tolerance.

| Status | Condition |
|---|---|
| `PRICE_MATCHED` | `|price_a − price_b| ≤ UNIT_PRICE_TOLERANCE` (0.01) |
| `PRICE_VARIANCE` | `|price_a − price_b| > UNIT_PRICE_TOLERANCE` |
| `PRICE_NOT_APPLICABLE` | Either price is None |

**Tolerance:** `UNIT_PRICE_TOLERANCE = 0.01` — allows for cent-level rounding differences, which are common when amounts are computed independently by different systems.

---

### Amount Status

Compares Source A line amount against Source B line amount using a tolerance.

| Status | Condition |
|---|---|
| `AMOUNT_MATCHED` | `|amt_a − amt_b| ≤ AMOUNT_TOLERANCE` (0.02) |
| `AMOUNT_VARIANCE` | `|amt_a − amt_b| > AMOUNT_TOLERANCE` |
| `AMOUNT_NOT_APPLICABLE` | Either amount is None |

**Tolerance:** `AMOUNT_TOLERANCE = 0.02` — slightly wider than price tolerance to accommodate compounding rounding effects (quantity × price).

---

## Overall Status Derivation

The overall reconciliation status is derived from the component statuses using a priority-based decision tree:

```
Input: identity_status, quantity_status, price_status, amount_status,
       match_method, confidence_score, transaction_type,
       is_unmatched_a, is_unmatched_b
```

### Step 1: Transaction Type Override

```
IF transaction_type == "CREDIT" → STATUS_CREDIT
IF transaction_type == "REVERSAL" → STATUS_REVERSAL
```

Credit and reversal transactions are always classified as such, regardless of other component statuses. They represent special processing paths.

---

### Step 2: Unmatched Side Classification

```
IF source_a_line_id is empty (only in B):
    → STATUS_MISSING_IN_SOURCE_A

IF source_b_line_id is empty (only in A):
    IF identity == IDENTITY_UNMATCHED:
        → STATUS_UNRESOLVED
    ELSE:
        → STATUS_MISSING_IN_SOURCE_B
```

Lines that exist in only one source are classified as missing in that source. If Source A has a line with no Source B counterpart and identity is unresolved, it is classified as `UNRESOLVED` rather than `MISSING_IN_SOURCE_B` to distinguish truly ambiguous cases.

---

### Step 3: Low-Confidence Fuzzy Review

```
IF match_method == FUZZY_NAME AND confidence < REVIEW_CONFIDENCE_FLOOR (80):
    → STATUS_FUZZY_MATCH_REVIEW
```

Fuzzy matches with confidence below 80 are routed to review regardless of quantity/price/amount agreement. This catches cases where the name similarity is marginal even though numbers happen to align.

---

### Step 4: Identity-Based Classification

```
IF identity == IDENTITY_UNMATCHED:
    → STATUS_UNRESOLVED

IF identity == IDENTITY_SUBSTITUTE:
    base = STATUS_MATCHED_WITH_SUBSTITUTE
ELSE:
    base = STATUS_MATCHED
```

---

### Step 5: Component Variance Override

Quantitative variances override the identity-based base status:

```
quantity_issue = quantity ∈ {QUANTITY_SHORTAGE, QUANTITY_EXCESS}
price_issue    = price == PRICE_VARIANCE
amount_issue   = amount == AMOUNT_VARIANCE

IF quantity_issue AND amount_issue:
    → STATUS_QUANTITY_AND_AMOUNT_DIFFERENCE

IF quantity_issue:
    → STATUS_QUANTITY_DIFFERENCE

IF price_issue:
    → STATUS_PRICE_DIFFERENCE

IF amount_issue:
    → STATUS_AMOUNT_DIFFERENCE
```

**Priority:** Quantity+Amount > Quantity alone > Price alone > Amount alone. The combined status takes precedence because it indicates a more complex discrepancy.

---

### Step 6: Default

```
IF identity == IDENTITY_SUBSTITUTE:
    → STATUS_MATCHED_WITH_SUBSTITUTE

ELSE:
    → STATUS_MATCHED
```

If no variances are detected and identity is confirmed, the line is classified as matched (either exact or substitute).

---

## Complete Status Reference

| Status | Description | Review Required | Trigger Condition |
|---|---|---|---|
| `MATCHED` | Exact or high-confidence match, all components agree | N | Identity matched, no variances |
| `MATCHED_WITH_SUBSTITUTE` | Equivalent product matched, all components agree | Y | Identity substitute, no variances |
| `MISSING_IN_SOURCE_A` | Item exists in Source B only | Y | Source A line_id empty |
| `MISSING_IN_SOURCE_B` | Item exists in Source A only | Y | Source B line_id empty, identity not unresolved |
| `ADDITIONAL_TRANSACTION` | Entire transaction exists in one source only | Y | Injected scenario; classified during matching |
| `ADDITIONAL_ITEM` | Extra line within a matched transaction | Y | Injected scenario; classified during matching |
| `QUANTITY_DIFFERENCE` | Matched item with quantity variance | Y | Quantity SHORTAGE or EXCESS |
| `PRICE_DIFFERENCE` | Matched item with price variance | Y | Price VARIANCE |
| `AMOUNT_DIFFERENCE` | Matched item with amount variance | Y | Amount VARIANCE |
| `QUANTITY_AND_AMOUNT_DIFFERENCE` | Both quantity and amount differ | Y | Quantity issue AND amount issue |
| `CREDIT` | Credit transaction | N | Transaction type = CREDIT |
| `REVERSAL` | Reversal transaction | N | Transaction type = REVERSAL |
| `FUZZY_MATCH_REVIEW` | Low-confidence fuzzy match | Y | FUZZY_NAME with confidence < 80 |
| `MASTER_DATA_EXCEPTION` | Product not in master data | Y | Injected scenario |
| `DUPLICATE_KEY` | Duplicate transaction/line key | Y | Injected scenario |
| `DATA_QUALITY_EXCEPTION` | Data quality issue prevents matching | Y | Injected scenario |
| `UNRESOLVED` | No classification possible | Y | Identity unmatched or ambiguous |

---

## Exception Statuses

The following statuses are considered exceptions (as opposed to clean reconciliations):

```python
EXCEPTION_STATUSES = frozenset({
    "MISSING_IN_SOURCE_A",
    "MISSING_IN_SOURCE_B",
    "ADDITIONAL_TRANSACTION",
    "ADDITIONAL_ITEM",
    "QUANTITY_DIFFERENCE",
    "PRICE_DIFFERENCE",
    "AMOUNT_DIFFERENCE",
    "QUANTITY_AND_AMOUNT_DIFFERENCE",
    "FUZZY_MATCH_REVIEW",
    "MASTER_DATA_EXCEPTION",
    "DUPLICATE_KEY",
    "DATA_QUALITY_EXCEPTION",
    "UNRESOLVED",
})
```

Lines with exception statuses contribute to `exception_rate_pct` and are eligible for the review queue.

---

## Review Routing Rules

A line is flagged for manual review (`review_required = 'Y'`) when its reconciliation status is in the exception set **or** when the status is `MATCHED_WITH_SUBSTITUTE` (which is not technically an exception but warrants human confirmation of the substitute product).

```python
review_required = "Y" if status in {
    MISSING_IN_SOURCE_A, MISSING_IN_SOURCE_B,
    ADDITIONAL_TRANSACTION, ADDITIONAL_ITEM,
    QUANTITY_DIFFERENCE, PRICE_DIFFERENCE,
    AMOUNT_DIFFERENCE, QUANTITY_AND_AMOUNT_DIFFERENCE,
    FUZZY_MATCH_REVIEW, MASTER_DATA_EXCEPTION,
    DUPLICATE_KEY, DATA_QUALITY_EXCEPTION,
    UNRESOLVED, MATCHED_WITH_SUBSTITUTE,
} else "N"
```

**Not review-required:** `MATCHED`, `CREDIT`, `REVERSAL` — these are clean outcomes.

---

## Tolerance Boundaries

| Tolerance | Value | Unit | Purpose |
|---|---|---|---|
| `UNIT_PRICE_TOLERANCE` | 0.01 | Currency unit | Allows cent-level rounding |
| `AMOUNT_TOLERANCE` | 0.02 | Currency unit | Allows compounding rounding in qty × price |
| `QUANTITY_TOLERANCE` | 0.0001 | Quantity | Effectively exact; catches floating-point artifacts |
| `REVIEW_CONFIDENCE_FLOOR` | 80.0 | Confidence score | Fuzzy matches below this always route to review |
| `FUZZY_ACCEPT_THRESHOLD` | 0.92 | Fuzzy score | Automatic acceptance boundary |
| `FUZZY_REVIEW_THRESHOLD` | 0.80 | Fuzzy score | Match-with-review boundary |

---

## Difference Computation

Each reconciliation result includes the raw numerical differences:

| Field | Formula | Precision |
|---|---|---|
| `quantity_difference` | `source_a_quantity − source_b_quantity` | 4 decimal places |
| `price_difference` | `source_a_unit_price − source_b_unit_price` | 4 decimal places |
| `amount_difference` | `source_a_amount − source_b_amount` | 4 decimal places |

When either side is None (missing or unparseable), the difference is `None`.
