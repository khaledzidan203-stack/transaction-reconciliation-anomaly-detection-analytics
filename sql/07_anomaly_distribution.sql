-- =============================================================================
-- 07_anomaly_distribution.sql
-- =============================================================================
-- Purpose: Anomaly type and severity distribution.
--          Shows how detected anomalies break down by their type (e.g. price
--          outlier, quantity spike) and severity level.
-- =============================================================================

SELECT
    anomaly_type,
    severity,
    reconciliation_status,
    COUNT(*)                                   AS anomaly_count,
    CAST(COUNT(*) AS DECIMAL(15,4))
        / NULLIF(SUM(COUNT(*)) OVER (), 0) * 100
                                               AS pct_of_total,
    CAST(COUNT(*) AS DECIMAL(15,4))
        / NULLIF(SUM(COUNT(*)) OVER (PARTITION BY anomaly_type), 0) * 100
                                               AS pct_within_type
FROM anomaly_results
GROUP BY anomaly_type, severity, reconciliation_status
ORDER BY
    anomaly_type,
    CASE severity
        WHEN 'critical' THEN 1
        WHEN 'high'     THEN 2
        WHEN 'medium'   THEN 3
        WHEN 'low'      THEN 4
        ELSE 5
    END;
