-- =============================================================================
-- 12_fuzzy_match_review_candidates.sql
-- =============================================================================
-- Purpose: Fuzzy matches in review band with details.
--          Isolates reconciliation lines that used a fuzzy matching method
--          and fall within the review confidence band, providing full detail
--          for analysts to confirm or reject the proposed match.
-- =============================================================================

SELECT
    r.source_a_line_id,
    r.source_a_transaction_id,
    r.source_b_line_id,
    r.source_b_transaction_id,
    r.match_method,
    CAST(r.confidence_score  AS DECIMAL(5,4))   AS confidence_score,
    r.reconciliation_status,
    r.identity_status,
    r.quantity_status,
    r.price_status,
    r.amount_status,
    r.source_a_product_id,
    r.source_b_product_id,
    r.source_a_product_name,
    r.source_b_product_name,
    CAST(r.source_a_quantity   AS DECIMAL(18,4)) AS source_a_quantity,
    CAST(r.source_b_quantity   AS DECIMAL(18,4)) AS source_b_quantity,
    CAST(r.source_a_unit_price AS DECIMAL(18,4)) AS source_a_unit_price,
    CAST(r.source_b_unit_price AS DECIMAL(18,4)) AS source_b_unit_price,
    CAST(r.source_a_amount     AS DECIMAL(18,4)) AS source_a_amount,
    CAST(r.source_b_amount     AS DECIMAL(18,4)) AS source_b_amount,
    CAST(r.quantity_difference  AS DECIMAL(18,4)) AS qty_diff,
    CAST(r.price_difference     AS DECIMAL(18,4)) AS price_diff,
    CAST(r.amount_difference    AS DECIMAL(18,4)) AS amount_diff,
    CAST(r.signed_exposure      AS DECIMAL(18,4)) AS signed_exposure,
    CAST(r.absolute_exposure    AS DECIMAL(18,4)) AS absolute_exposure,
    rq.priority                  AS review_priority,
    rq.anomaly_flags             AS anomaly_flags
FROM reconciliation_results r
INNER JOIN review_queue rq
        ON rq.line_key = r.source_a_line_id
WHERE LOWER(r.match_method) LIKE '%fuzzy%'
  AND r.review_required = 1 OR r.review_required = 'true'
  AND CAST(r.confidence_score AS DECIMAL(5,4)) BETWEEN 0.50 AND 0.85
ORDER BY CAST(r.confidence_score AS DECIMAL(5,4)) ASC,
         CAST(r.absolute_exposure AS DECIMAL(18,4)) DESC;
