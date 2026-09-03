-- =============================================================================
-- 01_reconciliation_summary.sql
-- =============================================================================
-- Purpose: Overall reconciliation status distribution with counts and exposure.
--          Provides a high-level view of how many lines landed in each
--          reconciliation bucket (matched, exception, unmatched) and the
--          total financial exposure associated with each status.
-- =============================================================================

SELECT
    reconciliation_status,
    COUNT(*)                                          AS line_count,
    CAST(COUNT(*) AS DECIMAL(15,4))
        / NULLIF(SUM(COUNT(*)) OVER (), 0) * 100    AS pct_of_total,
    SUM(CAST(absolute_exposure AS DECIMAL(18,4)))    AS total_absolute_exposure,
    SUM(CAST(unresolved_exposure AS DECIMAL(18,4)))  AS total_unresolved_exposure,
    SUM(CAST(review_exposure   AS DECIMAL(18,4)))    AS total_review_exposure,
    AVG(CAST(confidence_score  AS DECIMAL(5,4)))     AS avg_confidence_score,
    SUM(CASE WHEN review_required = 1 OR review_required = 'true'
             THEN 1 ELSE 0 END)                      AS review_required_count
FROM reconciliation_results
GROUP BY reconciliation_status
ORDER BY line_count DESC;
