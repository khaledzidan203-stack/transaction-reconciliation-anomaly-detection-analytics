# Anomaly Detection

## Overview

The anomaly detection engine (`src/anomaly_detection.py`) applies deterministic rules to identify suspicious or unusual patterns in reconciliation results. Anomalies are **separate from** reconciliation status — a fully matched transaction can still carry an anomaly (e.g., unusually high amount), and an unmatched transaction may have no anomalies beyond its status.

Each anomaly record includes the line key, anomaly type, severity, description, and the reconciliation status of the underlying line.

---

## Anomaly Detection Rules

### Rule 1: HIGH_VALUE_OUTLIER

**Trigger:** The absolute exposure of a line exceeds the population mean by a configurable multiplier.

```
IF absolute_exposure > mean(absolute_exposure) × ANOMALY_HIGH_AMOUNT_MULTIPLIER:
    → anomaly_type: HIGH_VALUE_OUTLIER
    → severity: HIGH
```

**Configuration:**
| Parameter | Value | Description |
|---|---|---|
| `ANOMALY_HIGH_AMOUNT_MULTIPLIER` | 5.0 | Multiple of population mean |

**Description format:** `"Amount {abs_exp:.2f} exceeds {multiplier}x population mean {mean:.2f}"`

**Rationale:** Transactions with exposure far above the population average are statistically unusual and may indicate data entry errors, duplicate processing, or genuine high-value exceptions that warrant closer examination.

**Example:**
```
Population mean absolute exposure: 45.67
Line absolute exposure: 523.40
523.40 > 45.67 × 5.0 = 228.35
→ HIGH_VALUE_OUTLIER, severity: HIGH, "Amount 523.40 exceeds 5.0x population mean 45.67"
```

---

### Rule 2: LOW_CONFIDENCE_MATCH

**Trigger:** A match was found but the confidence score is below a threshold.

```
IF 0 < confidence_score < ANOMALY_LOW_CONFIDENCE_THRESHOLD:
    → anomaly_type: LOW_CONFIDENCE_MATCH
    → severity: MEDIUM
```

**Configuration:**
| Parameter | Value | Description |
|---|---|---|
| `ANOMALY_LOW_CONFIDENCE_THRESHOLD` | 75.0 | Confidence below this is anomalous |

**Description format:** `"Match confidence {score:.1f} below threshold {threshold}"`

**Rationale:** Low-confidence matches (e.g., POSSIBLE_SUBSTITUTE at 70, or FUZZY_NAME in the REVIEW band at 80–92) carry inherent uncertainty. Flagging them as anomalies ensures analysts pay extra attention to the quality of these matches.

**Note:** Confidence of 0 (UNMATCHED) is excluded from this rule — it is covered by Rule 6 (UNRESOLVED_TRANSACTION).

---

### Rule 3: DATA_QUALITY_FAILURE

**Trigger:** The reconciliation status is `DATA_QUALITY_EXCEPTION`, indicating that a data quality issue prevented proper matching.

```
IF reconciliation_status == "DATA_QUALITY_EXCEPTION":
    → anomaly_type: DATA_QUALITY_FAILURE
    → severity: CRITICAL
```

**Description:** `"Data quality check failed on this line"`

**Rationale:** Data quality failures (malformed identifiers, invalid numerics) are the most severe anomaly type because they indicate structural problems in the source data that may cascade into incorrect reconciliation outcomes. CRITICAL severity ensures they appear at the top of the review queue.

---

### Rule 4: MASTER_DATA_MISSING

**Trigger:** The reconciliation status is `MASTER_DATA_EXCEPTION`, indicating that a transaction references a product not found in the master catalog.

```
IF reconciliation_status == "MASTER_DATA_EXCEPTION":
    → anomaly_type: MASTER_DATA_MISSING
    → severity: HIGH
```

**Description:** `"Product not found in master data"`

**Rationale:** Missing master records prevent product identification and may indicate a new product not yet cataloged, a data migration gap, or an identifier corruption. HIGH severity reflects the operational importance of resolving master data gaps.

---

### Rule 5: DUPLICATE_KEY

**Trigger:** The reconciliation status is `DUPLICATE_KEY`, indicating that a transaction or line key appears more than once in the same source.

```
IF reconciliation_status == "DUPLICATE_KEY":
    → anomaly_type: DUPLICATE_KEY
    → severity: HIGH
```

**Description:** `"Duplicate transaction or line key detected"`

**Rationale:** Duplicate keys violate the uniqueness assumption of transaction identifiers. They may indicate double-processing, system errors, or data pipeline bugs. HIGH severity ensures they are investigated promptly.

---

### Rule 6: UNRESOLVED_TRANSACTION

**Trigger:** The reconciliation status is `UNRESOLVED`, meaning no matching path was found.

```
IF reconciliation_status == "UNRESOLVED":
    → anomaly_type: UNRESOLVED_TRANSACTION
    → severity: MEDIUM
```

**Description:** `"No matching path found for this transaction line"`

**Rationale:** Unresolved transactions represent the residual of the matching engine — lines that could not be matched at any level. MEDIUM severity reflects that these are expected in any reconciliation but should be monitored for volume trends.

---

### Rule 7: MISSING_COUNTERPART

**Trigger:** The reconciliation status is `MISSING_IN_SOURCE_A` or `MISSING_IN_SOURCE_B`, meaning a transaction exists in only one source system.

```
IF reconciliation_status in {"MISSING_IN_SOURCE_A", "MISSING_IN_SOURCE_B"}:
    → anomaly_type: MISSING_COUNTERPART
    → severity: LOW
```

**Description format:** `"Status: {status}"`

**Rationale:** Missing counterparts are common in reconciliation (timing differences, source-specific transactions). LOW severity reflects that they are typically benign but should be tracked for patterns (e.g., a specific branch consistently having one-sided transactions).

---

## Severity Levels

| Severity | Numeric Order | Description | Review Queue Impact |
|---|---|---|---|
| `CRITICAL` | 0 (highest) | Immediate attention required; structural data problem | Lines with CRITICAL anomalies always get CRITICAL priority in the review queue |
| `HIGH` | 1 | Significant deviation; requires investigation | Elevates review queue priority (subject to exposure amount) |
| `MEDIUM` | 2 | Notable deviation; may require attention | Standard review priority |
| `LOW` | 3 | Informational; minor deviation | Lowest review priority |

---

## Rule Configuration Parameters

| Parameter | Default | Location | Used By |
|---|---|---|---|
| `ANOMALY_HIGH_AMOUNT_MULTIPLIER` | 5.0 | `config.py` | Rule 1: HIGH_VALUE_OUTLIER |
| `ANOMALY_HIGH_QUANTITY_MULTIPLIER` | 5.0 | `config.py` | Reserved for future quantity outlier rule |
| `ANOMALY_PRICE_OUTLIER_MULTIPLIER` | 3.0 | `config.py` | Reserved for future price outlier rule |
| `ANOMALY_HIGH_RATE_THRESHOLD` | 0.25 | `config.py` | Reserved for future high-rate anomaly rule |
| `ANOMALY_LOW_CONFIDENCE_THRESHOLD` | 75.0 | `config.py` | Rule 2: LOW_CONFIDENCE_MATCH |
| `ANOMALY_FREQUENCY_MULTIPLIER` | 3.0 | `config.py` | Reserved for future frequency anomaly rule |

**Note:** Parameters marked "Reserved" are defined in `config.py` but not yet wired into active detection rules. They represent the intended expansion path for the anomaly engine.

---

## Independence from Reconciliation Status

Anomalies and reconciliation statuses serve different purposes:

| Dimension | Reconciliation Status | Anomaly Detection |
|---|---|---|
| **Purpose** | Classify the match quality and discrepancy type | Flag unusual patterns |
| **Scope** | Every line gets exactly one status | A line may have zero, one, or multiple anomalies |
| **Direction** | Status describes *what happened* | Anomaly describes *what's unusual* |
| **Example** | A MATCHED line with 0 exposure → status = MATCHED, no anomaly | A MATCHED line with very high exposure → status = MATCHED, anomaly = HIGH_VALUE_OUTLIER |

A single line can trigger multiple anomaly rules simultaneously. For example, a `DATA_QUALITY_EXCEPTION` line with an unusually high amount would generate both a `DATA_QUALITY_FAILURE` (CRITICAL) and a `HIGH_VALUE_OUTLIER` (HIGH) anomaly.

---

## Anomaly Output Schema

| Field | Type | Description |
|---|---|---|
| `line_key` | string | Source line identifier (from `source_a_line_id` or `source_b_line_id`) |
| `anomaly_type` | string | One of 7 anomaly type names |
| `severity` | string | `CRITICAL`, `HIGH`, `MEDIUM`, or `LOW` |
| `description` | string | Human-readable explanation with specific values |
| `reconciliation_status` | string | Reconciliation status of the line |

---

## Population Statistics

Rule 1 (HIGH_VALUE_OUTLIER) relies on population-level statistics computed at detection time:

```python
amounts = reconciliation_results["absolute_exposure"].dropna()
mean_amount = amounts.mean()
```

The mean is computed across all reconciliation lines in the current run. This means the threshold is relative to the current dataset, not an absolute value. In a production deployment, this would typically be replaced with a rolling historical baseline.
