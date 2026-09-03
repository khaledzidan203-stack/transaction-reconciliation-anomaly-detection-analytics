-- =============================================================================
-- 06_data_quality_summary.sql
-- =============================================================================
-- Purpose: Data quality issue summary by severity and type.
--          Aggregates recorded data quality issues to reveal the most common
--          defect categories and their severity distribution across tables.
-- =============================================================================

SELECT
    "table"           AS source_table,
    field,
    issue_type,
    severity,
    COUNT(*)                                AS issue_count,
    COUNT(DISTINCT record_key)              AS affected_records
FROM data_quality_issues
GROUP BY "table", field, issue_type, severity
ORDER BY
    CASE severity
        WHEN 'critical' THEN 1
        WHEN 'high'     THEN 2
        WHEN 'medium'   THEN 3
        WHEN 'low'      THEN 4
        ELSE 5
    END,
    issue_count DESC;
