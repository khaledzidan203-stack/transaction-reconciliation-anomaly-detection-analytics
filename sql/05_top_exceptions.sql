-- =============================================================================
-- 05_top_exceptions.sql
-- =============================================================================
-- Purpose: Top exception lines by absolute exposure.
--          Surfaces the costliest reconciliation exceptions so analysts can
--          prioritise investigation and remediation efforts.
-- =============================================================================

SELECT
    r.source_a_line_id,
    r.source_a_transaction_id,
    r.source_b_line_id,
    r.source_b_transaction_id,
    r.match_method,
    r.reconciliation_status,
    r.identity_status,
    r.quantity_status,
    r.price_status,
    r.amount_status,
    r.source_a_product_name,
    r.source_b_product_name,
    CAST(r.source_a_amount     AS DECIMAL(18,4))  AS source_a_amount,
    CAST(r.source_b_amount     AS DECIMAL(18,4))  AS source_b_amount,
    CAST(r.source_a_quantity   AS DECIMAL(18,4))  AS source_a_quantity,
    CAST(r.source_b_quantity   AS DECIMAL(18,4))  AS source_b_quantity,
    CAST(r.source_a_unit_price AS DECIMAL(18,4))  AS source_a_unit_price,
    CAST(r.source_b_unit_price AS DECIMAL(18,4))  AS source_b_unit_price,
    CAST(r.quantity_difference  AS DECIMAL(18,4))  AS qty_diff,
    CAST(r.price_difference     AS DECIMAL(18,4))  AS price_diff,
    CAST(r.amount_difference    AS DECIMAL(18,4))  AS amount_diff,
    CAST(r.absolute_exposure    AS DECIMAL(18,4))  AS absolute_exposure,
    CAST(r.signed_exposure      AS DECIMAL(18,4))  AS signed_exposure,
    CAST(r.confidence_score     AS DECIMAL(5,4))   AS confidence_score
FROM reconciliation_results r
WHERE r.reconciliation_status <> 'matched'
   OR r.reconciliation_status IS NULL
ORDER BY CAST(r.absolute_exposure AS DECIMAL(18,4)) DESC
LIMIT 50;
