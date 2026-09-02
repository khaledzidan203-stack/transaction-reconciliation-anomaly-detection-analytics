"""Tests for reconciliation, exposure, anomaly detection, KPIs, review queue."""

from pathlib import Path

import pandas as pd
import pytest
from src.config import STATUS_MATCHED, STATUS_UNRESOLVED
from src.ingestion import load_csvs
from src.synthetic_data_generator import generate_all
from src.pipeline import run_pipeline


class TestReconciliationStatuses:
    @pytest.fixture(autouse=True)
    def _run(self, tmp_path: Path):
        self.data_dir = tmp_path / "data"
        self.output_dir = tmp_path / "outputs"
        generate_all(self.data_dir)
        self.result = run_pipeline(self.data_dir, self.output_dir)
        self.recon = pd.read_csv(self.output_dir / "reconciliation_results.csv")

    def test_recon_has_component_statuses(self):
        for col in ["identity_status", "quantity_status", "price_status", "amount_status"]:
            assert col in self.recon.columns

    def test_review_required_is_y_or_n(self):
        values = set(self.recon["review_required"].unique())
        assert values <= {"Y", "N"}

    def test_matched_lines_have_high_confidence(self):
        matched = self.recon[self.recon["reconciliation_status"] == STATUS_MATCHED]
        if len(matched) > 0:
            assert matched["confidence_score"].mean() > 80


class TestExposure:
    @pytest.fixture(autouse=True)
    def _run(self, tmp_path: Path):
        self.data_dir = tmp_path / "data"
        self.output_dir = tmp_path / "outputs"
        generate_all(self.data_dir)
        self.result = run_pipeline(self.data_dir, self.output_dir)
        self.recon = pd.read_csv(self.output_dir / "reconciliation_results.csv")

    def test_exposure_columns_present(self):
        for col in ["signed_exposure", "absolute_exposure"]:
            assert col in self.recon.columns

    def test_absolute_exposure_non_negative(self):
        assert all(self.recon["absolute_exposure"] >= 0)


class TestAnomalies:
    @pytest.fixture(autouse=True)
    def _run(self, tmp_path: Path):
        self.data_dir = tmp_path / "data"
        self.output_dir = tmp_path / "outputs"
        generate_all(self.data_dir)
        self.result = run_pipeline(self.data_dir, self.output_dir)
        self.anomalies = pd.read_csv(self.output_dir / "anomaly_results.csv")

    def test_anomalies_have_severity(self):
        if len(self.anomalies) > 0:
            assert "severity" in self.anomalies.columns
            valid = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
            assert set(self.anomalies["severity"].unique()) <= valid


class TestKPIs:
    @pytest.fixture(autouse=True)
    def _run(self, tmp_path: Path):
        self.data_dir = tmp_path / "data"
        self.output_dir = tmp_path / "outputs"
        generate_all(self.data_dir)
        self.result = run_pipeline(self.data_dir, self.output_dir)

    def test_kpis_in_valid_range(self):
        kpis = self.result["kpis"]
        assert 0 <= kpis["match_rate_pct"] <= 100
        assert 0 <= kpis["exception_rate_pct"] <= 100
        assert kpis["total_lines"] > 0
        assert kpis["total_absolute_exposure"] >= 0

    def test_kpi_by_branch_written(self):
        df = pd.read_csv(self.output_dir / "kpi_by_branch.csv")
        assert len(df) > 0
        assert "branch_id" in df.columns

    def test_kpi_by_month_written(self):
        df = pd.read_csv(self.output_dir / "kpi_by_month.csv")
        assert len(df) > 0
        assert "month_key" in df.columns


class TestReviewQueue:
    @pytest.fixture(autouse=True)
    def _run(self, tmp_path: Path):
        self.data_dir = tmp_path / "data"
        self.output_dir = tmp_path / "outputs"
        generate_all(self.data_dir)
        self.result = run_pipeline(self.data_dir, self.output_dir)
        self.review = pd.read_csv(self.output_dir / "review_queue.csv")

    def test_review_has_priority(self):
        if len(self.review) > 0:
            valid = {"CRITICAL", "HIGH", "MEDIUM", "LOW"}
            assert set(self.review["priority"].unique()) <= valid

    def test_review_sorted_by_priority(self):
        if len(self.review) > 1:
            order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
            priorities = self.review["priority"].map(order).tolist()
            # Should be non-decreasing
            assert all(priorities[i] <= priorities[i + 1] for i in range(len(priorities) - 1))
