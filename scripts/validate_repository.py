from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PROTECTED_CORE = {
    "src/config.py": "0f14a3fd1db4dfa5fc56b996168884c7f214185f",
    "src/matching.py": "5cc9c6deb02a61fbc22fd43c471177c253eb6150",
    "src/reconciliation.py": "aaea7a0b4d1ed3599a6bc33039cd664a958eadc6",
    "src/exposure.py": "2ad52d04e4e0f61b0ad4a09471b12054cd96dd6e",
    "src/synthetic_data_generator.py": "27d1db5279c9b3fe513008c8aa29d16b558276ba",
    "src/review_queue.py": "65a910f6a5ec617ee81fa247751b8a261f250a02",
    "src/anomaly_detection.py": "db77ee31c19865a4cac27e392840e2ea6221d476",
    "data/sample/generation_manifest.json": "16c6518e8c969307c0feaa393bd37343a66f33a9",
    "outputs/examples/kpi_summary.csv": "c2a2336f214e4ea247f8bdec4ba944c28c9153cc",
    "dashboard/reconciliation_dashboard.html": "68824ec5e71d5109a8a042386a5ce607c8985b7e",
}

EXPECTED_KPIS = {
    "total_lines": "2424",
    "matched_lines": "1170",
    "exception_lines": "1174",
    "match_rate_pct": "48.27",
    "exception_rate_pct": "48.43",
    "total_absolute_exposure": "818612.86",
    "unresolved_exposure": "256344.73",
    "average_confidence": "89.20",
    "review_required_count": "1182",
    "review_rate_pct": "48.76",
}

EXPECTED_MANIFEST_ROWS = {
    "product_master": 150,
    "branch_master": 10,
    "employee_master": 32,
    "source_a_headers": 2305,
    "source_a_lines": 2385,
    "source_b_headers": 2095,
    "source_b_lines": 2095,
    "expected_scenarios": 2260,
}

REQUIRED_DOCS = [
    "README.md",
    "PROJECT_NOTES.md",
    "docs/README.md",
    "docs/PROJECT_INDEX.md",
    "docs/CASE_STUDY.md",
    "docs/TECHNICAL_WALKTHROUGH.md",
    "docs/PROJECT_EVIDENCE_MAP.md",
    "docs/FINAL_RELEASE_VALIDATION.md",
    "docs/powerbi/README.md",
    "docs/assets/Transaction Reconciliation Analytics Dashboard.png",
]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    header = f"blob {len(data)}\0".encode("utf-8")
    return hashlib.sha1(header + data).hexdigest()


def validate_core() -> None:
    for rel, expected in PROTECTED_CORE.items():
        path = ROOT / rel
        require(path.exists(), f"Missing protected core file: {rel}")
        actual = git_blob_sha(path)
        require(actual == expected, f"Protected core changed: {rel} ({actual} != {expected})")


def validate_manifest() -> None:
    manifest = json.loads((ROOT / "data/sample/generation_manifest.json").read_text(encoding="utf-8"))
    require(manifest["seed"] == 20260902, "Unexpected synthetic-data seed")
    for name, rows in EXPECTED_MANIFEST_ROWS.items():
        require(manifest["files"][name]["rows"] == rows, f"Manifest row count changed for {name}")


def validate_kpis() -> None:
    with (ROOT / "outputs/examples/kpi_summary.csv").open(encoding="utf-8", newline="") as handle:
        row = next(csv.DictReader(handle))
    for key, expected in EXPECTED_KPIS.items():
        require(row[key] == expected, f"KPI baseline changed for {key}: {row[key]} != {expected}")


def validate_presentation() -> None:
    for rel in REQUIRED_DOCS:
        require((ROOT / rel).exists(), f"Missing required file: {rel}")

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    require("Featured Portfolio" not in readme, "README contains old portfolio cross-promotion block")
    require("Primary roles demonstrated" not in readme, "README contains role-targeting language")
    require("portfolio demonstration" not in readme.lower(), "README contains old portfolio-demonstration language")
    require("Transaction%20Reconciliation%20Analytics%20Dashboard.png" in readme, "README hero image link missing")
    require("## Quick Start" in readme, "README Quick Start missing")

    pbi_boundary = (ROOT / "docs/powerbi/README.md").read_text(encoding="utf-8")
    require("design specifications" in pbi_boundary.lower(), "Power BI implementation boundary not documented")

    sql_files = sorted((ROOT / "sql").glob("*.sql"))
    require(len(sql_files) == 12, f"Expected 12 SQL analytical scripts, found {len(sql_files)}")

    dashboard = ROOT / "dashboard/reconciliation_dashboard.html"
    require(dashboard.stat().st_size > 20_000, "HTML dashboard appears incomplete")


def main() -> None:
    validate_core()
    validate_manifest()
    validate_kpis()
    validate_presentation()

    print("PASS | protected reconciliation core")
    print("PASS | deterministic synthetic manifest")
    print("PASS | retained KPI baseline")
    print("PASS | documentation and presentation contract")
    print("PASS | 12 SQL analytical scripts")
    print("PASS | implemented HTML dashboard")
    print("REPOSITORY VALIDATION PASS")


if __name__ == "__main__":
    main()
