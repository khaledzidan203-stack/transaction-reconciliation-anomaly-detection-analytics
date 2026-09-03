-- =============================================================================
-- 08_review_queue_analysis.sql
-- =============================================================================
-- Purpose: Review queue breakdown by priority and status.
--          Helps operations teams understand workload distribution and
--          prioritise manual review of flagged reconciliation lines.
-- =============================================================================

SELECT
    priority,
    reconciliation_status,
    COUNT(*)                                             AS item_count,
    AVG(CAST(confidence_score AS DECIMAL(5,4)))          AS avg_confidence_score,
    MIN(CAST(confidence_score AS DECIMAL(5,4)))          AS min_confidence_score,
    MAX(CAST(confidence_score AS DECIMAL(5,4)))          AS max_confidence_score,
    SUM(CAST(absolute_exposure AS DECIMAL(18,4)))        AS total_absolute_exposure,
    AVG(CAST(absolute_exposure AS DECIMAL(18,4)))        AS avg_absolute_exposure,
    COUNT(DISTINCT anomaly_flags)                        AS distinct_anomaly_flag_count
FROM review_queue
GROUP BY priority, reconciliation_status
ORDER BY
    priority,
    reconciliation_status;
