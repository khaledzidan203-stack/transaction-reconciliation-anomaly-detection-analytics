# Matching Methodology

## Overview

The matching engine (`src/matching.py`) implements an 8-level hierarchical matcher that pairs Source A transaction lines with Source B transaction lines. The hierarchy is strict: the first level that produces a match determines the result, and lower levels are never attempted for that line.

Every match result is fully explainable — it records the method used, a confidence score, and (for fuzzy matches) the raw similarity score and threshold band.

---

## Match Hierarchy

| Priority | Method | Confidence | Trigger Condition |
|---|---|---|---|
| 1 | `EXACT_PRIMARY_ID` | 100.0 | A.reference_id normalized == B.transaction_id normalized **AND** A.product_id normalized == B.product_id normalized |
| 2 | `EXACT_BARCODE` | 97.0 | A.barcode normalized (digits only) == B.barcode normalized, both non-empty |
| 3 | `EXACT_PRODUCT_CODE` | 95.0 | A.product_code normalized (separators stripped) == B.product_code normalized, both non-empty |
| 4 | `NORMALIZED_NAME` | 90.0 | A.product_name normalized (uppercase, noise removed, unit-split) == B.product_name normalized, both non-empty |
| 5 | `FUZZY_NAME` | score × 100 | Token-sort or partial ratio ≥ 0.80; two bands: ACCEPT (≥0.92) and REVIEW (0.80–0.92) |
| 6 | `GENERIC_STRENGTH` | 85.0 | A.generic_name normalized == B.generic_name normalized **AND** A.product_name ≠ B.product_name (different brand) |
| 7 | `POSSIBLE_SUBSTITUTE` | 70.0 | Fuzzy generic name match ≥ 0.70, same category, different product |
| 8 | `UNMATCHED` | 0.0 | No match found at any level |

### Why These Confidence Values

- **100** (Primary ID): Cross-referenced by transaction ID and product ID — highest possible certainty
- **97** (Barcode): EAN-13 barcodes are globally unique; the 3-point gap accounts for rare barcode reuse across product variants
- **95** (Product Code): Internal codes may occasionally overlap across systems; the 5-point gap reflects this risk
- **90** (Normalized Name): Deterministic normalization eliminates spacing/casing differences; 10-point gap covers rare homonym collisions
- **score × 100** (Fuzzy): Variable — reflects the actual string similarity, preserving gradation
- **85** (Generic Strength): Same active ingredient and strength but different brand — therapeutically equivalent but commercially distinct
- **70** (Possible Substitute): Similar generic category but different strength/brand — flagged for review by default
- **0** (Unmatched): No evidence of any relationship

---

## Level-by-Level Detail

### Level 1: EXACT_PRIMARY_ID

**Condition:** Source A's `reference_id` (normalized) equals Source B's `transaction_id` (normalized) **and** the `product_id` values match after normalization.

**Normalization applied:**
- `normalize_identifier()` — strips spaces, hyphens, slashes, dots; uppercases

**Example:**
```
Source A: reference_id = "TXN-B-000456", product_id = "PRD-0042"
Source B: transaction_id = "TXN-B-000456", product_id = "PRD-0042"
→ Normalized: "TXNB000456" == "TXNB000456" AND "PRD0042" == "PRD0042"
→ Match: EXACT_PRIMARY_ID, confidence 100
```

This level uses a `b_by_txn_id` lookup index for O(1) retrieval.

---

### Level 2: EXACT_BARCODE

**Condition:** Source A's barcode (normalized to digits only) equals Source B's barcode (normalized to digits only), both non-empty.

**Normalization applied:**
- `normalize_barcode()` — strips all non-digit characters; handles Excel float-to-string conversion (e.g., `1234567890123.0` → `1234567890123`)

**Example:**
```
Source A: barcode = "2000000004213"
Source B: barcode = "2000000004213", product_id = "PRD-9999" (different from A)
→ Match: EXACT_BARCODE, confidence 97
```

This level uses a `b_by_barcode` lookup index.

---

### Level 3: EXACT_PRODUCT_CODE

**Condition:** Source A's product_code (normalized) equals Source B's product_code (normalized), both non-empty.

**Normalization applied:**
- `normalize_identifier()` — strips separators, uppercases

**Example:**
```
Source A: product_code = "PC-ZEN0042"
Source B: product_code = "PC-ZEN0042", product_id = "PRD-8001" (different), barcode = different
→ Normalized: "PCZEN0042" == "PCZEN0042"
→ Match: EXACT_PRODUCT_CODE, confidence 95
```

This level uses a `b_by_code` lookup index.

---

### Level 4: NORMALIZED_NAME

**Condition:** Source A's product_name (normalized) equals Source B's product_name (normalized), both non-empty.

**Normalization applied by `normalize_product_name()`:**
1. Unicode NFKC normalization + combining mark removal
2. Uppercase conversion
3. Unicode hyphen/slash collapse to ASCII equivalents
4. **Unit splitting**: glued number-unit pairs like `750ML` → `750 ML`
5. Non-alphanumeric character removal (except dots)
6. Noise token removal: PACK, BOX, UNIT, PCS, EACH, THE, AND, WITH, OF, FOR, NEW, etc.
7. Whitespace collapse

**Example:**
```
Source A: "ZENITH All Purpose Cleaner 750ML"
Source B: "ZENITH All Purpose Cleaner 750 ML"
→ Both normalize to: "ZENITH ALL PURPOSE CLEANER 750 ML"
→ Match: NORMALIZED_NAME, confidence 90
```

This level uses a `b_by_norm_name` lookup index.

---

### Level 5: FUZZY_NAME

**Condition:** The best fuzzy similarity score between normalized product names ≥ 0.80.

**Algorithm:**
1. Build candidate pool from inverted token index (tokens ≥ 3 characters)
2. For each candidate, compute `max(token_sort_ratio, partial_ratio)` using `rapidfuzz`
3. Select the highest-scoring candidate

**Threshold bands:**

| Band | Score Range | Outcome |
|---|---|---|
| ACCEPT | ≥ 0.92 | Match accepted; confidence = score × 100 |
| REVIEW | 0.80 – 0.92 | Match accepted but flagged for review; confidence = score × 100 |
| (no match) | < 0.80 | Falls through to Level 6 |

**Example:**
```
Source A: "ZENITH Glass Spray 500 ML" → normalized: "ZENITH GLASS SPRAY 500 ML"
Source B: "ZENITH Glass SprayX 500 ML" → normalized: "ZENITH GLASS SPRAYX 500 ML"
→ token_sort_ratio ≈ 0.96
→ Match: FUZZY_NAME, confidence 96.0, band: ACCEPT
```

**Performance:** The inverted token index (`b_name_token_index`) maps each token (≥3 chars) from Source B product names to a set of row indices. Source A tokens retrieve candidate indices, avoiding an O(n²) scan of all B-lines.

---

### Level 6: GENERIC_STRENGTH

**Condition:** Source A's `generic_name` (normalized) equals Source B's `generic_name` (normalized) **and** the full `product_name` (normalized) differs (different brand).

**Example:**
```
Source A: product_name = "ZENITH Glass Spray 500 ML", generic_name = "Glass Spray 500 ML"
Source B: product_name = "AURORA Glass Spray 500 ML", generic_name = "Glass Spray 500 ML"
→ Generic keys match, product names differ (different brand)
→ Match: GENERIC_STRENGTH, confidence 85
```

This level uses a `b_by_generic` lookup index.

---

### Level 7: POSSIBLE_SUBSTITUTE

**Condition:** Fuzzy match on generic name ≥ 0.70, using the first token of the Source A generic name to filter candidates from the generic index.

**Algorithm:**
1. Extract the first token from A's normalized generic name
2. Find all B-line indices whose generic key contains that token
3. Compute fuzzy score between A's generic and each candidate's generic
4. Accept if best score ≥ 0.70

**Example:**
```
Source A: generic = "Glass Spray 250 ML"
Source B: generic = "Glass Spray 500 ML"
→ First token "GLASS" matches; fuzzy generic score ≥ 0.70
→ Match: POSSIBLE_SUBSTITUTE, confidence 70
```

---

### Level 8: UNMATCHED

When no level produces a match, the line is classified as `UNMATCHED` with confidence 0. These lines are routed to the review queue with appropriate priority.

---

## B-Line Consumption Rule

Once a Source B line is matched to a Source A line, it is added to the `consumed_b_indices` set and cannot be matched to any other Source A line. This prevents many-to-one matches and ensures each B-line is used at most once.

**Implication:** The order in which Source A lines are processed affects which B-lines are available for later matches. Source A lines are processed in DataFrame index order.

---

## Fuzzy Matching Approach

The fuzzy matching engine uses `rapidfuzz`, a fast Python wrapper around the C++ RapidFuzz library.

**Two similarity metrics are computed; the maximum is used:**

| Metric | Description | Strength |
|---|---|---|
| `token_sort_ratio` | Sorts tokens alphabetically, then computes Levenshtein ratio | Handles word-order differences |
| `partial_ratio` | Finds the best matching substring | Handles one name being a subset of the other |

**Pre-processing for fuzzy matching:**
Both names are pre-normalized via `normalize_product_name()` (uppercase, unit-split, noise removed) before entering the fuzzy comparison. This means the fuzzy engine only deals with residual differences that normalization could not eliminate (typos, abbreviations, brand variants).

---

## Threshold Configuration

| Parameter | Value | Location | Description |
|---|---|---|---|
| `FUZZY_ACCEPT_THRESHOLD` | 0.92 | `config.py` | Minimum score for automatic acceptance |
| `FUZZY_REVIEW_THRESHOLD` | 0.80 | `config.py` | Minimum score for match with review; below this, no match |
| `REVIEW_CONFIDENCE_FLOOR` | 80.0 | `config.py` | Matched pairs with confidence below this always route to review |
| Substitute fuzzy floor | 0.70 | `matching.py` | Minimum fuzzy generic score for POSSIBLE_SUBSTITUTE |

---

## Match Output Schema

Each Source A line produces one row in the match results:

| Field | Type | Description |
|---|---|---|
| `source_a_line_id` | string | Source A line identifier |
| `source_a_transaction_id` | string | Source A transaction identifier |
| `source_a_product_id` | string | Source A product identifier |
| `source_b_line_id` | string | Matched Source B line identifier (empty if UNMATCHED) |
| `source_b_transaction_id` | string | Matched Source B transaction identifier (empty if UNMATCHED) |
| `source_b_product_id` | string | Matched Source B product identifier (empty if UNMATCHED) |
| `match_method` | string | One of 8 match method names |
| `confidence_score` | float | 0.0–100.0 |
| `fuzzy_score` | float | Raw fuzzy similarity (0.0–1.0; 0.0 for non-fuzzy matches) |
| `fuzzy_threshold_band` | string | `ACCEPT`, `REVIEW`, or empty (for non-fuzzy matches) |
