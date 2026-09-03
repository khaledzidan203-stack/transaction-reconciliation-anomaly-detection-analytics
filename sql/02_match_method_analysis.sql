-- =============================================================================
-- 02_match_method_analysis.sql
-- =============================================================================
-- Purpose: Match method distribution with average confidence.
--          Shows how often each matching algorithm (exact, barcode, fuzzy,
--          etc.) was used and how confident those matches are on average.
-- =============================================================================

SELECT
    match_method,
    reconciliation_status,
    COUNT(*)                                           AS line_count,
    AVG(CAST(confidence_score AS DECIMAL(5,4)))        AS avg_confidence_score,
    MIN(CAST(confidence_score AS DECIMAL(5,4)))        AS min_confidence_score,
    MAX(CAST(confidence_score AS DECIMAL(5,4)))        AS max_confidence_score,
    SUM(CAST(absolute_exposure AS DECIMAL(18,4)))      AS total_absolute_exposure,
    SUM(CAST(quantity_difference AS DECIMAL(18,4)))     AS total_qty_difference,
    SUM(CAST(price_difference   AS DECIMAL(18,4)))     AS total_price_difference,
    SUM(CAST(amount_difference  AS DECIMAL(18,4)))     AS total_amount_difference
FROM reconciliation_results
GROUP BY match_method, reconciliation_status
ORDER BY match_method, reconciliation_status;
