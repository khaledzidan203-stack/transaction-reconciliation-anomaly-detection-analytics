"""Pipeline orchestrator: run the full reconciliation analytics pipeline.

Loads data, validates schemas, checks data quality, builds master maps,
matches lines, reconciles, computes exposure, detects anomalies,
computes KPIs, builds the review queue and writes all outputs.
"""

from __future__ import annotations

from typing import Any

from .anomaly_detection import detect_anomalies
from .data_quality import run_data_quality
from .exposure import compute_exposure
from .ingestion import load_csvs
from .kpis import compute_kpis, compute_kpis_by_branch, compute_kpis_by_month
from .master_mapping import build_master_maps
from .matching import match_lines
from .reconciliation import reconcile
from .reporting import write_all_outputs
from .review_queue import build_review_queue
from .schema_validation import validate_all_schemas


def run_pipeline(data_dir: Any = None, output_dir: Any = None) -> dict[str, Any]:
    """Execute the full pipeline end to end.

    Parameters
    ----------
    data_dir:
        Directory containing input CSVs. Defaults to ``SAMPLE_DIR``.
    output_dir:
        Directory for output files. Defaults to ``EXAMPLE_OUTPUT_DIR``.

    Returns
    -------
    dict
        Pipeline result metadata including KPIs and output paths.
    """
    # 1. Load and normalize
    dataset = load_csvs(data_dir)

    # 2. Schema validation
    schema_issues = validate_all_schemas(dataset)

    # 3. Data quality
    dq_issues = run_data_quality(dataset)

    # 4. Master mapping
    master_maps = build_master_maps(dataset)

    # 5. Matching
    match_results = match_lines(dataset.source_a_lines, dataset.source_b_lines)

    # 6. Reconciliation
    recon_results = reconcile(
        match_results,
        dataset.source_a_lines,
        dataset.source_b_lines,
        dataset.source_a_headers,
        dataset.source_b_headers,
    )

    # 7. Exposure
    recon_with_exposure = compute_exposure(recon_results)

    # 8. Anomaly detection
    anomalies = detect_anomalies(recon_with_exposure, dataset.product_master)

    # 9. KPIs
    kpis = compute_kpis(recon_with_exposure)
    kpi_branch = compute_kpis_by_branch(
        recon_with_exposure, dataset.source_a_headers, dataset.source_b_headers)
    kpi_month = compute_kpis_by_month(
        recon_with_exposure, dataset.source_a_headers, dataset.source_b_headers)

    # 10. Review queue
    review = build_review_queue(recon_with_exposure, anomalies)

    # 11. Write outputs
    output_paths = write_all_outputs(
        recon_with_exposure, dq_issues, anomalies, review,
        kpis, kpi_branch, kpi_month, output_dir,
    )

    return {
        "kpis": kpis,
        "output_paths": output_paths,
        "total_reconciliation_lines": len(recon_with_exposure),
        "total_data_quality_issues": len(dq_issues),
        "total_anomalies": len(anomalies),
        "total_review_items": len(review),
    }


if __name__ == "__main__":
    result = run_pipeline()
    print("Pipeline complete.")
    for k, v in result["kpis"].items():
        print(f"  {k}: {v}")
