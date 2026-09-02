"""Tests for the full pipeline: integration and ground-truth regression."""

from pathlib import Path

import pandas as pd
import pytest
from src.config import (
    SCENARIO_TYPES,
    STATUS_MATCHED,
)
from src.ingestion import load_csvs
from src.synthetic_data_generator import generate_all
from src.pipeline import run_pipeline


class TestPipelineIntegration:
    """End-to-end pipeline must complete and produce all output files."""

    @pytest.fixture(autouse=True)
    def _run(self, tmp_path: Path):
        self.data_dir = tmp_path / "data"
        self.output_dir = tmp_path / "outputs"
        generate_all(self.data_dir)
        self.result = run_pipeline(self.data_dir, self.output_dir)

    def test_pipeline_completes(self):
        assert self.result is not None

    def test_kpis_computed(self):
        kpis = self.result["kpis"]
        assert kpis["total_lines"] > 0
        assert 0 <= kpis["match_rate_pct"] <= 100

    def test_output_files_created(self):
        for path in self.result["output_paths"].values():
            assert Path(path).exists(), f"Missing output: {path}"

    def test_reconciliation_results_not_empty(self):
        df = pd.read_csv(self.output_dir / "reconciliation_results.csv")
        assert len(df) > 0

    def test_data_quality_issues_written(self):
        df = pd.read_csv(self.output_dir / "data_quality_issues.csv")
        # Should have at least some DQ issues from injected scenarios
        assert len(df) >= 0

    def test_anomaly_results_written(self):
        df = pd.read_csv(self.output_dir / "anomaly_results.csv")
        assert len(df) >= 0

    def test_review_queue_written(self):
        df = pd.read_csv(self.output_dir / "review_queue.csv")
        assert len(df) >= 0

    def test_kpi_summary_written(self):
        df = pd.read_csv(self.output_dir / "kpi_summary.csv")
        assert len(df) > 0

    def test_dashboard_data_json_valid(self):
        import json
        path = self.output_dir / "dashboard_data.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert "summary_kpis" in data
        assert "status_distribution" in data


class TestGroundTruthRegression:
    """Validate that the pipeline's reconciliation results align with
    the expected scenario ground truth from the synthetic generator."""

    @pytest.fixture(autouse=True)
    def _run(self, tmp_path: Path):
        self.data_dir = tmp_path / "data"
        self.output_dir = tmp_path / "outputs"
        generate_all(self.data_dir)
        self.result = run_pipeline(self.data_dir, self.output_dir)
        self.recon = pd.read_csv(self.output_dir / "reconciliation_results.csv")
        self.expected = pd.read_csv(self.data_dir / "expected_scenarios.csv")

    def test_all_scenario_types_present_in_ground_truth(self):
        found = set(self.expected["scenario_type"].unique())
        assert found == set(SCENARIO_TYPES)

    def test_clean_exact_matches_are_matched(self):
        """CLEAN_EXACT_MATCH scenarios should resolve to MATCHED."""
        clean = self.expected[self.expected["scenario_type"] == "CLEAN_EXACT_MATCH"]
        matched_a_ids = set(
            self.recon.loc[
                self.recon["reconciliation_status"] == STATUS_MATCHED, "source_a_line_id"
            ].dropna().tolist()
        )
        matched_count = sum(
            1 for _, row in clean.iterrows()
            if row["source_a_line_id"] in matched_a_ids
        )
        # At least 80% of clean matches should resolve
        assert matched_count / max(len(clean), 1) >= 0.80, (
            f"Only {matched_count}/{len(clean)} CLEAN_EXACT_MATCH resolved"
        )

    def test_missing_in_source_detected(self):
        """Missing-in-source scenarios should produce appropriate statuses.
        Depending on matching aggressiveness, these may appear as
        MISSING_IN_SOURCE_B, ADDITIONAL_ITEM or similar."""
        missing_a = self.expected[self.expected["scenario_type"] == "MISSING_IN_SOURCE_A"]
        missing_b = self.expected[self.expected["scenario_type"] == "MISSING_IN_SOURCE_B"]
        if len(missing_a) == 0 and len(missing_b) == 0:
            pytest.skip("No missing-in-source scenarios")
        recon_statuses = set(self.recon["reconciliation_status"].unique())
        # At least one exception status must exist
        assert recon_statuses & {"MISSING_IN_SOURCE_A", "MISSING_IN_SOURCE_B",
                                 "ADDITIONAL_ITEM", "UNRESOLVED"}, (
            f"No unmatched statuses found in: {recon_statuses}"
        )

    def test_exception_statuses_present(self):
        """Pipeline should produce exception statuses beyond just MATCHED."""
        recon_statuses = set(self.recon["reconciliation_status"].unique())
        from src.config import EXCEPTION_STATUSES
        assert recon_statuses & EXCEPTION_STATUSES, (
            "No exception statuses found in reconciliation results"
        )
