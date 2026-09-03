-- =============================================================================
-- 03_exposure_by_branch.sql
-- =============================================================================
-- Purpose: Financial exposure breakdown by branch.
--          Joins reconciliation results with branch master to attribute
--          exposure, match rates, and review counts to each physical branch.
-- =============================================================================

SELECT
    b.branch_id,
    b.branch_name,
    b.city,
    b.region,
    COUNT(*)                                            AS total_lines,
    SUM(CASE WHEN r.reconciliation_status = 'matched'
             THEN 1 ELSE 0 END)                         AS matched_lines,
    SUM(CASE WHEN r.reconciliation_status = 'exception'
             THEN 1 ELSE 0 END)                         AS exception_lines,
    SUM(CASE WHEN r.reconciliation_status = 'unmatched'
             THEN 1 ELSE 0 END)                         AS unmatched_lines,
    CAST(SUM(CASE WHEN r.reconciliation_status = 'matched' THEN 1 ELSE 0 END)
         AS DECIMAL(15,4))
        / NULLIF(CAST(COUNT(*) AS DECIMAL(15,4)), 0) * 100
                                                       AS match_rate_pct,
    SUM(CAST(r.absolute_exposure  AS DECIMAL(18,4)))   AS total_absolute_exposure,
    SUM(CAST(r.unresolved_exposure AS DECIMAL(18,4)))  AS total_unresolved_exposure,
    SUM(CAST(r.review_exposure    AS DECIMAL(18,4)))   AS total_review_exposure,
    SUM(CASE WHEN r.review_required = 1 OR r.review_required = 'true'
             THEN 1 ELSE 0 END)                        AS review_required_count
FROM reconciliation_results r
LEFT JOIN branch_master b
       ON r.source_a_transaction_id IN (
               SELECT transaction_id FROM source_a_transaction_headers WHERE branch_id = b.branch_id
           )
GROUP BY b.branch_id, b.branch_name, b.city, b.region
ORDER BY total_absolute_exposure DESC;
