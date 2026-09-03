-- =============================================================================
-- 10_product_category_reconciliation.sql
-- =============================================================================
-- Purpose: Reconciliation performance by product category.
--          Joins through product_master to evaluate which product categories
--          have the highest exception rates and financial exposure.
-- =============================================================================

SELECT
    p.category,
    COUNT(*)                                                 AS total_lines,
    SUM(CASE WHEN r.reconciliation_status = 'matched'
             THEN 1 ELSE 0 END)                              AS matched_lines,
    SUM(CASE WHEN r.reconciliation_status = 'exception'
             THEN 1 ELSE 0 END)                              AS exception_lines,
    SUM(CASE WHEN r.reconciliation_status = 'unmatched'
             THEN 1 ELSE 0 END)                              AS unmatched_lines,
    CAST(SUM(CASE WHEN r.reconciliation_status = 'matched' THEN 1 ELSE 0 END)
         AS DECIMAL(15,4))
        / NULLIF(CAST(COUNT(*) AS DECIMAL(15,4)), 0) * 100  AS match_rate_pct,
    SUM(CAST(r.absolute_exposure   AS DECIMAL(18,4)))        AS total_absolute_exposure,
    SUM(CAST(r.unresolved_exposure AS DECIMAL(18,4)))        AS total_unresolved_exposure,
    AVG(CAST(r.confidence_score    AS DECIMAL(5,4)))         AS avg_confidence_score,
    SUM(CAST(r.quantity_difference AS DECIMAL(18,4)))         AS total_qty_difference,
    SUM(CAST(r.price_difference    AS DECIMAL(18,4)))         AS total_price_difference,
    SUM(CASE WHEN r.review_required = 1 OR r.review_required = 'true'
             THEN 1 ELSE 0 END)                              AS review_required_count
FROM reconciliation_results r
LEFT JOIN product_master p
       ON r.source_a_product_id = p.product_id
GROUP BY p.category
ORDER BY total_absolute_exposure DESC;
