"""Tests for src.utils: deterministic IO, rounding and hashing."""

import json
from pathlib import Path

import pandas as pd
import pytest
from src.config import ROUNDING_DECIMALS
from src.utils import (
    describe_frame,
    ensure_dir,
    file_sha256,
    frame_fingerprint,
    iter_sorted,
    read_csv,
    read_json,
    round_money,
    write_csv,
    write_json,
)


class TestRoundMoney:
    def test_basic_rounding(self):
        assert round_money(1.005) == round(1.005, ROUNDING_DECIMALS)

    def test_integer(self):
        assert round_money(10) == 10.0

    def test_none_returns_zero(self):
        assert round_money(None) == 0.0

    def test_string_number(self):
        assert round_money("3.14159") == 3.14


class TestCsvIO:
    def test_write_read_roundtrip(self, tmp_path: Path):
        df = pd.DataFrame({"a": ["1", "2"], "b": ["3.14", "0.99"]})
        path = tmp_path / "test.csv"
        write_csv(df, path)
        result = read_csv(path)
        assert list(result.columns) == ["a", "b"]
        assert len(result) == 2

    def test_deterministic_hash(self, tmp_path: Path):
        df = pd.DataFrame({"x": ["hello", "world"]})
        path = tmp_path / "det.csv"
        write_csv(df, path)
        h1 = file_sha256(path)
        write_csv(df, path)
        h2 = file_sha256(path)
        assert h1 == h2

    def test_missing_file_sha256(self):
        assert file_sha256(Path("/nonexistent/file.csv")) == ""

    def test_frame_fingerprint_stable(self):
        df = pd.DataFrame({"a": ["1"], "b": ["2"]})
        assert frame_fingerprint(df) == frame_fingerprint(df)

    def test_frame_fingerprint_detects_change(self):
        df1 = pd.DataFrame({"a": ["1"]})
        df2 = pd.DataFrame({"a": ["2"]})
        assert frame_fingerprint(df1) != frame_fingerprint(df2)


class TestJsonIO:
    def test_write_read_roundtrip(self, tmp_path: Path):
        payload = {"key": "value", "num": 42}
        path = tmp_path / "test.json"
        write_json(payload, path)
        result = read_json(path)
        assert result == payload

    def test_sorted_keys(self, tmp_path: Path):
        payload = {"z": 1, "a": 2}
        path = tmp_path / "sorted.json"
        write_json(payload, path)
        text = path.read_text(encoding="utf-8")
        assert text.index('"a"') < text.index('"z"')


class TestDescribeFrame:
    def test_describe(self):
        df = pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]})
        desc = describe_frame(df)
        assert desc["rows"] == 3
        assert desc["columns"] == 2
        assert desc["column_names"] == ["x", "y"]


class TestIterSorted:
    def test_basic(self):
        assert iter_sorted([3, 1, 2]) == [1, 2, 3]

    def test_with_none(self):
        result = iter_sorted([3, None, 1])
        # None sorts last because (True, ...) > (False, ...)
        assert result[-1] is None
        assert result[0] == 1
