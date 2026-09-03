-- =============================================================================
-- 04_exposure_by_month.sql
-- =============================================================================
-- Purpose: Monthly exposure trend analysis.
--          Tracks how financial exposure and reconciliation quality evolve
--          over time by aggregating metrics per calendar month.
-- =============================================================================

SELECT
    SUBSTR(CAST(h.transaction_date AS VARCHAR(10)), 1, 7)  AS transaction_month,
    COUNT(*)                                                 AS total_lines,
    SUM(CASE WHEN r.reconciliation_status = 'matched'
             THEN 1 ELSE 0 END)                              AS matched_lines,
    SUM(CASE WHEN r.reconciliation_status = 'exception'
             THEN 1 ELSE 0 END)                              AS exception_lines,
    SUM(CASE WHEN r.reconciliation_status = 'unmatched'
             THEN 1 ELSE 0 END)                              AS unmatched_lines,
    CAST(SUM(CASE WHEN r.reconciliation_status = 'matched' THEN 1 ELSE 0 END)
         AS DECIMAL(15,4))
        / NULLIF(CAST(COUNT(*) AS DECIMAL(15,4)), 0) * 100 AS match_rate_pct,
    SUM(CAST(r.absolute_exposure   AS DECIMAL(18,4)))       AS total_absolute_exposure,
    SUM(CAST(r.unresolved_exposure AS DECIMAL(18,4)))       AS total_unresolved_exposure,
    SUM(CAST(r.review_exposure     AS DECIMAL(18,4)))       AS total_review_exposure,
    AVG(CAST(r.confidence_score    AS DECIMAL(5,4)))        AS avg_confidence_score,
    SUM(CASE WHEN r.review_required = 1 OR r.review_required = 'true'
             THEN 1 ELSE 0 END)                             AS review_required_count
FROM reconciliation_results r
LEFT JOIN source_a_transaction_headers h
       ON r.source_a_transaction_id = h.transaction_id
GROUP BY SUBSTR(CAST(h.transaction_date AS VARCHAR(10)), 1, 7)
ORDER BY transaction_month;
