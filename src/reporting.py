"""Reporting: write all pipeline outputs to disk.

Produces CSV and JSON outputs for reconciliation results, data quality
issues, anomalies, review queue, KPIs and dashboard data.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from .config import (
    EXAMPLE_OUTPUT_DIR,
    FILE_ANOMALIES,
    FILE_DASHBOARD_DATA,
    FILE_DATA_QUALITY,
    FILE_KPI_BY_BRANCH,
    FILE_KPI_BY_MONTH,
    FILE_KPI_SUMMARY,
    FILE_RECONCILIATION_RESULTS,
    FILE_REVIEW_QUEUE,
)
from .utils import ensure_dir, write_csv, write_json


def write_reconciliation_results(frame: pd.DataFrame, output_dir: Any = None) -> str:
    path = (output_dir or EXAMPLE_OUTPUT_DIR) / FILE_RECONCILIATION_RESULTS
    write_csv(frame, path)
    return str(path)


def write_data_quality_issues(frame: pd.DataFrame, output_dir: Any = None) -> str:
    path = (output_dir or EXAMPLE_OUTPUT_DIR) / FILE_DATA_QUALITY
    write_csv(frame, path)
    return str(path)


def write_anomaly_results(frame: pd.DataFrame, output_dir: Any = None) -> str:
    path = (output_dir or EXAMPLE_OUTPUT_DIR) / FILE_ANOMALIES
    write_csv(frame, path)
    return str(path)


def write_review_queue(frame: pd.DataFrame, output_dir: Any = None) -> str:
    path = (output_dir or EXAMPLE_OUTPUT_DIR) / FILE_REVIEW_QUEUE
    write_csv(frame, path)
    return str(path)


def write_kpi_summary(kpis: dict[str, Any], output_dir: Any = None) -> str:
    path = (output_dir or EXAMPLE_OUTPUT_DIR) / FILE_KPI_SUMMARY
    df = pd.DataFrame([kpis])
    write_csv(df, path)
    return str(path)


def write_kpi_by_branch(frame: pd.DataFrame, output_dir: Any = None) -> str:
    path = (output_dir or EXAMPLE_OUTPUT_DIR) / FILE_KPI_BY_BRANCH
    write_csv(frame, path)
    return str(path)


def write_kpi_by_month(frame: pd.DataFrame, output_dir: Any = None) -> str:
    path = (output_dir or EXAMPLE_OUTPUT_DIR) / FILE_KPI_BY_MONTH
    write_csv(frame, path)
    return str(path)


def write_dashboard_data(
    kpis: dict[str, Any],
    kpi_branch: pd.DataFrame,
    kpi_month: pd.DataFrame,
    recon: pd.DataFrame,
    anomalies: pd.DataFrame,
    review: pd.DataFrame,
    output_dir: Any = None,
) -> str:
    """Write a JSON bundle for dashboard consumption."""
    path = (output_dir or EXAMPLE_OUTPUT_DIR) / FILE_DASHBOARD_DATA
    payload = {
        "summary_kpis": kpis,
        "kpi_by_branch": kpi_branch.to_dict(orient="records") if not kpi_branch.empty else [],
        "kpi_by_month": kpi_month.to_dict(orient="records") if not kpi_month.empty else [],
        "status_distribution": recon["reconciliation_status"].value_counts().to_dict() if not recon.empty else {},
        "match_method_distribution": recon["match_method"].value_counts().to_dict() if not recon.empty else {},
        "anomaly_summary": anomalies["anomaly_type"].value_counts().to_dict() if not anomalies.empty else {},
        "review_priority_distribution": review["priority"].value_counts().to_dict() if not review.empty else {},
    }
    write_json(payload, path)
    return str(path)


def write_all_outputs(
    recon: pd.DataFrame,
    dq: pd.DataFrame,
    anomalies: pd.DataFrame,
    review: pd.DataFrame,
    kpis: dict[str, Any],
    kpi_branch: pd.DataFrame,
    kpi_month: pd.DataFrame,
    output_dir: Any = None,
) -> dict[str, str]:
    """Write every output file and return a map of name -> path."""
    out = output_dir or EXAMPLE_OUTPUT_DIR
    ensure_dir(out)
    paths: dict[str, str] = {}
    paths["reconciliation_results"] = write_reconciliation_results(recon, out)
    paths["data_quality_issues"] = write_data_quality_issues(dq, out)
    paths["anomaly_results"] = write_anomaly_results(anomalies, out)
    paths["review_queue"] = write_review_queue(review, out)
    paths["kpi_summary"] = write_kpi_summary(kpis, out)
    paths["kpi_by_branch"] = write_kpi_by_branch(kpi_branch, out)
    paths["kpi_by_month"] = write_kpi_by_month(kpi_month, out)
    paths["dashboard_data"] = write_dashboard_data(
        kpis, kpi_branch, kpi_month, recon, anomalies, review, out)
    return paths
