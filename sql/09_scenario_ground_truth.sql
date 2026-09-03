-- =============================================================================
-- 09_scenario_ground_truth.sql
-- =============================================================================
-- Purpose: Compare expected vs actual reconciliation statuses.
--          Joins the expected_scenarios table with reconciliation_results to
--          validate whether the reconciliation engine produced the expected
--          outcomes for each test scenario.
-- =============================================================================

SELECT
    e.scenario_id,
    e.scenario_type,
    e.source_a_transaction_id,
    e.source_b_transaction_id,
    e.source_a_line_id,
    e.source_b_line_id,
    e.expected_match_method,
    r.match_method                  AS actual_match_method,
    e.expected_reconciliation_status,
    r.reconciliation_status         AS actual_reconciliation_status,
    e.expected_review_required,
    r.review_required               AS actual_review_required,
    CASE
        WHEN e.expected_reconciliation_status = r.reconciliation_status
         AND (e.expected_match_method = r.match_method
              OR e.expected_match_method IS NULL)
            THEN 'PASS'
        ELSE 'FAIL'
    END                             AS status_result,
    CASE
        WHEN e.expected_reconciliation_status <> r.reconciliation_status
            THEN 'Status mismatch: expected ' || COALESCE(e.expected_reconciliation_status, 'NULL')
              || ' got ' || COALESCE(r.reconciliation_status, 'NULL')
        WHEN e.expected_match_method <> r.match_method
             AND e.expected_match_method IS NOT NULL
            THEN 'Method mismatch: expected ' || e.expected_match_method
              || ' got ' || COALESCE(r.match_method, 'NULL')
        ELSE NULL
    END                             AS discrepancy_detail,
    e.expected_notes
FROM expected_scenarios e
LEFT JOIN reconciliation_results r
       ON (e.source_a_line_id  = r.source_a_line_id
        OR e.source_b_line_id  = r.source_b_line_id)
ORDER BY e.scenario_id;
