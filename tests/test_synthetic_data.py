"""Tests for the synthetic data generator: determinism and structure."""

from pathlib import Path

import pandas as pd
import pytest
from src.config import RANDOM_SEED, SAMPLE_DIR
from src.synthetic_data_generator import generate_all


class TestGeneratorDeterminism:
    """Two consecutive runs must produce byte-identical output."""

    def test_deterministic_csvs(self, tmp_path: Path):
        dir1 = tmp_path / "run1"
        dir2 = tmp_path / "run2"
        generate_all(dir1)
        generate_all(dir2)

        for fname in [
            "product_master.csv", "branch_master.csv", "employee_master.csv",
            "source_a_transaction_headers.csv", "source_a_transaction_lines.csv",
            "source_b_transaction_headers.csv", "source_b_transaction_lines.csv",
            "expected_scenarios.csv",
        ]:
            h1 = (dir1 / fname).read_bytes()
            h2 = (dir2 / fname).read_bytes()
            assert h1 == h2, f"{fname} differs between runs"


class TestMasterDataStructure:
    @pytest.fixture(autouse=True)
    def _generate(self, tmp_path: Path):
        self.manifest = generate_all(tmp_path)
        self.data_dir = tmp_path

    def test_product_master_count(self):
        df = pd.read_csv(self.data_dir / "product_master.csv")
        assert len(df) == 150

    def test_branch_master_count(self):
        df = pd.read_csv(self.data_dir / "branch_master.csv")
        assert len(df) == 10

    def test_employee_master_count(self):
        df = pd.read_csv(self.data_dir / "employee_master.csv")
        assert len(df) == 32

    def test_products_have_valid_barcodes(self):
        from src.normalization import is_valid_ean13
        df = pd.read_csv(self.data_dir / "product_master.csv")
        for bc in df["barcode"]:
            assert is_valid_ean13(bc), f"Invalid barcode: {bc}"

    def test_expected_scenarios_covers_all_types(self):
        from src.config import SCENARIO_TYPES
        df = pd.read_csv(self.data_dir / "expected_scenarios.csv")
        found_types = set(df["scenario_type"].unique())
        assert found_types == set(SCENARIO_TYPES)


class TestTransactionDataStructure:
    @pytest.fixture(autouse=True)
    def _generate(self, tmp_path: Path):
        generate_all(tmp_path)
        self.data_dir = tmp_path

    def test_source_a_has_lines(self):
        df = pd.read_csv(self.data_dir / "source_a_transaction_lines.csv")
        assert len(df) > 0

    def test_source_b_has_lines(self):
        df = pd.read_csv(self.data_dir / "source_b_transaction_lines.csv")
        assert len(df) > 0

    def test_line_ids_unique_format(self):
        df = pd.read_csv(self.data_dir / "source_a_transaction_lines.csv")
        for lid in df["line_id"]:
            assert lid.startswith("TXN-"), f"Unexpected line_id format: {lid}"
