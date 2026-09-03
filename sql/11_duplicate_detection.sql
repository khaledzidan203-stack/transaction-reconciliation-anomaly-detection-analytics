-- =============================================================================
-- 11_duplicate_detection.sql
-- =============================================================================
-- Purpose: Find duplicate transactions and lines across sources.
--          Identifies potential duplicate records within each source and
--          across sources by looking for identical transaction keys and
--          repeated line-level detail combinations.
-- =============================================================================

-- Part A: Duplicate transaction headers within Source A
SELECT
    'Source A - Headers'               AS duplicate_scope,
    transaction_id,
    branch_id,
    employee_id,
    transaction_date,
    transaction_type,
    COUNT(*)                            AS occurrence_count,
    SUM(CAST(total_amount AS DECIMAL(18,4))) AS total_amount_sum
FROM source_a_transaction_headers
GROUP BY transaction_id, branch_id, employee_id, transaction_date, transaction_type
HAVING COUNT(*) > 1

UNION ALL

-- Part B: Duplicate transaction headers within Source B
SELECT
    'Source B - Headers'               AS duplicate_scope,
    transaction_id,
    branch_id,
    employee_id,
    transaction_date,
    transaction_type,
    COUNT(*)                            AS occurrence_count,
    SUM(CAST(total_amount AS DECIMAL(18,4))) AS total_amount_sum
FROM source_b_transaction_headers
GROUP BY transaction_id, branch_id, employee_id, transaction_date, transaction_type
HAVING COUNT(*) > 1

UNION ALL

-- Part C: Duplicate transaction lines within Source A
SELECT
    'Source A - Lines'                  AS duplicate_scope,
    CAST(transaction_id AS VARCHAR(50)),
    product_id,
    product_code,
    barcode,
    product_name,
    quantity,
    COUNT(*)                            AS occurrence_count,
    SUM(CAST(amount AS DECIMAL(18,4)))  AS total_amount_sum
FROM source_a_transaction_lines
GROUP BY transaction_id, product_id, product_code, barcode, product_name, quantity
HAVING COUNT(*) > 1

UNION ALL

-- Part D: Duplicate transaction lines within Source B
SELECT
    'Source B - Lines'                  AS duplicate_scope,
    CAST(transaction_id AS VARCHAR(50)),
    product_id,
    product_code,
    barcode,
    product_name,
    quantity,
    COUNT(*)                            AS occurrence_count,
    SUM(CAST(amount AS DECIMAL(18,4)))  AS total_amount_sum
FROM source_b_transaction_lines
GROUP BY transaction_id, product_id, product_code, barcode, product_name, quantity
HAVING COUNT(*) > 1

ORDER BY duplicate_scope, occurrence_count DESC;
