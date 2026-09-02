# Test Cases

> Full test case documentation will be added in Phase 8.

## Test Coverage

- Exact primary-ID matching
- Barcode and product-code matching
- Normalized and fuzzy name matching
- Equivalent product and substitute classification
- Missing source scenarios (A and B)
- Additional transaction and item scenarios
- Quantity, price, and amount variance handling
- Credit and reversal handling
- Duplicate-key handling
- Missing master records
- Invalid numeric handling
- Exposure calculation accuracy
- Confidence threshold behavior
- Manual-review logic
- Deterministic synthetic data generation
- Tolerance boundaries
- Anomaly severity classification
- Regression cases

## Running Tests

```bash
pytest tests/ -v
```
