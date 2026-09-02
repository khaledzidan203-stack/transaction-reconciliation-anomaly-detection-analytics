"""Shared helpers: deterministic IO, rounding and content hashing."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from .config import ROUNDING_DECIMALS

# Columns whose floating point representation must be written with a fixed
# number of decimals so that repeated generator runs produce identical bytes.
FLOAT_FORMAT: str = f"%.{ROUNDING_DECIMALS}f"


def ensure_dir(path: Path) -> Path:
    """Create *path* if missing and return it."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def round_money(value: Any) -> float:
    """Round a monetary value to the configured number of decimals."""
    try:
        return round(float(value), ROUNDING_DECIMALS)
    except (TypeError, ValueError):
        return 0.0


def write_csv(frame: pd.DataFrame, path: Path) -> Path:
    """Write a dataframe deterministically.

    Determinism rules:
    * no index column
    * fixed decimal formatting for floats
    * LF line endings (enforced by .gitattributes as well)
    * UTF-8 without BOM
    """
    ensure_dir(path.parent)
    frame.to_csv(
        path,
        index=False,
        float_format=FLOAT_FORMAT,
        encoding="utf-8",
        lineterminator="\n",
    )
    return path


def read_csv(path: Path, **kwargs: Any) -> pd.DataFrame:
    """Read a CSV, treating empty strings as missing values consistently."""
    defaults: dict[str, Any] = {
        "keep_default_na": False,
        "na_values": [""],
        "dtype": "object",
        "encoding": "utf-8",
    }
    defaults.update(kwargs)
    return pd.read_csv(path, **defaults)


def file_sha256(path: Path) -> str:
    """Return the SHA-256 digest of a file, or an empty string if missing."""
    if not path.exists():
        return ""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65_536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def frame_fingerprint(frame: pd.DataFrame) -> str:
    """Return a stable digest of a dataframe's content and column order."""
    payload = frame.to_csv(index=False, float_format=FLOAT_FORMAT, lineterminator="\n")
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def write_json(payload: Any, path: Path) -> Path:
    """Write JSON deterministically (sorted keys, fixed indent)."""
    ensure_dir(path.parent)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )
    return path


def read_json(path: Path) -> Any:
    """Read a JSON document."""
    return json.loads(path.read_text(encoding="utf-8"))


def describe_frame(frame: pd.DataFrame) -> dict[str, Any]:
    """Small structural description used by manifests and tests."""
    return {
        "rows": int(frame.shape[0]),
        "columns": int(frame.shape[1]),
        "column_names": list(frame.columns),
    }


def iter_sorted(values: Iterable[Any]) -> list[Any]:
    """Deterministic sorted list, tolerating mixed None values."""
    return sorted(values, key=lambda item: (item is None, str(item)))
