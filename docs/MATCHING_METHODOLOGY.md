# Matching Methodology

> Full matching methodology documentation will be added in Phase 8.

## Matching Hierarchy

| Priority | Method | Description |
|---|---|---|
| 1 | Exact Primary ID | Transaction reference number matches exactly |
| 2 | Exact Barcode | Product barcode matches exactly |
| 3 | Exact Product Code | Product master code matches exactly |
| 4 | Normalized Name | Deterministic name normalization produces identical keys |
| 5 | Fuzzy Name | Constrained fuzzy string matching above confidence threshold |
| 6 | Equivalent Product | Same active ingredient / generic strength match |
| 7 | Possible Substitute | Low-confidence match flagged for review |
| 8 | Unmatched | No match found — routed to manual review |

## Match Output Fields

Every match result preserves:
- source_a_transaction_id
- source_b_transaction_id
- source_a_line_id
- source_b_line_id
- source_a_product_code
- source_b_product_code
- match_method
- confidence_score
- supporting_evidence
- identity_status
- quantity_status
- price_status
- amount_status
- reconciliation_status
- reconciliation_reason
- review_required

## Fuzzy Matching

Fuzzy matching uses constrained string similarity with:
- Minimum confidence threshold
- Maximum length difference
- Token-level comparison
- Brand name awareness

Fuzzy matching only runs after deterministic rules fail.
