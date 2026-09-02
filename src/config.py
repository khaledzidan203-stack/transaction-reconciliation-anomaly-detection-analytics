"""Central configuration for the reconciliation analytics pipeline.

Every tunable value in the project lives here so that behaviour is
reproducible, documented and testable. No secrets, no environment
specific paths and no real business identifiers appear in this module.
"""

from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------------------
# Paths (always repository relative, never machine specific)
# ---------------------------------------------------------------------------

PROJECT_ROOT: Path = Path(__file__).resolve().parents[1]
DATA_DIR: Path = PROJECT_ROOT / "data"
SAMPLE_DIR: Path = DATA_DIR / "sample"
OUTPUT_DIR: Path = PROJECT_ROOT / "outputs"
EXAMPLE_OUTPUT_DIR: Path = OUTPUT_DIR / "examples"

# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------

RANDOM_SEED: int = 20260902

# ---------------------------------------------------------------------------
# Synthetic dataset scale
# ---------------------------------------------------------------------------

N_BRANCHES: int = 10
N_EMPLOYEES: int = 32
N_PRODUCTS: int = 150
N_BASE_TRANSACTIONS: int = 2_200
MONTHS: tuple[str, ...] = ("2026-01", "2026-02", "2026-03", "2026-04")

# ---------------------------------------------------------------------------
# Source system labels (generic, non identifying)
# ---------------------------------------------------------------------------

SOURCE_A: str = "SOURCE_A"
SOURCE_B: str = "SOURCE_B"

SOURCE_A_LABEL: str = "POS System"
SOURCE_B_LABEL: str = "Reference System"

# ---------------------------------------------------------------------------
# Match methods, in hierarchy order
# ---------------------------------------------------------------------------

MATCH_EXACT_PRIMARY_ID: str = "EXACT_PRIMARY_ID"
MATCH_EXACT_BARCODE: str = "EXACT_BARCODE"
MATCH_EXACT_PRODUCT_CODE: str = "EXACT_PRODUCT_CODE"
MATCH_NORMALIZED_NAME: str = "NORMALIZED_NAME"
MATCH_FUZZY_NAME: str = "FUZZY_NAME"
MATCH_GENERIC_STRENGTH: str = "GENERIC_STRENGTH_EQUIVALENT"
MATCH_POSSIBLE_SUBSTITUTE: str = "POSSIBLE_SUBSTITUTE"
MATCH_NONE: str = "UNMATCHED"

MATCH_METHOD_HIERARCHY: tuple[str, ...] = (
    MATCH_EXACT_PRIMARY_ID,
    MATCH_EXACT_BARCODE,
    MATCH_EXACT_PRODUCT_CODE,
    MATCH_NORMALIZED_NAME,
    MATCH_FUZZY_NAME,
    MATCH_GENERIC_STRENGTH,
    MATCH_POSSIBLE_SUBSTITUTE,
    MATCH_NONE,
)

# ---------------------------------------------------------------------------
# Confidence scores
# ---------------------------------------------------------------------------

CONFIDENCE_PRIMARY_ID: float = 100.0
CONFIDENCE_BARCODE: float = 97.0
CONFIDENCE_PRODUCT_CODE: float = 95.0
CONFIDENCE_NORMALIZED_NAME: float = 90.0
CONFIDENCE_GENERIC_STRENGTH: float = 85.0
CONFIDENCE_POSSIBLE_SUBSTITUTE: float = 70.0
CONFIDENCE_UNMATCHED: float = 0.0

# ---------------------------------------------------------------------------
# Tolerances (documented and boundary tested)
# ---------------------------------------------------------------------------

FUZZY_ACCEPT_THRESHOLD: float = 0.92
FUZZY_REVIEW_THRESHOLD: float = 0.80

UNIT_PRICE_TOLERANCE: float = 0.01
AMOUNT_TOLERANCE: float = 0.02
QUANTITY_TOLERANCE: float = 0.0001

ROUNDING_DECIMALS: int = 2

# Confidence below this value always routes a matched pair to manual review.
REVIEW_CONFIDENCE_FLOOR: float = 80.0

# ---------------------------------------------------------------------------
# Reconciliation statuses
# ---------------------------------------------------------------------------

STATUS_MATCHED: str = "MATCHED"
STATUS_MATCHED_WITH_SUBSTITUTE: str = "MATCHED_WITH_SUBSTITUTE"
STATUS_MISSING_IN_SOURCE_A: str = "MISSING_IN_SOURCE_A"
STATUS_MISSING_IN_SOURCE_B: str = "MISSING_IN_SOURCE_B"
STATUS_ADDITIONAL_TRANSACTION: str = "ADDITIONAL_TRANSACTION"
STATUS_ADDITIONAL_ITEM: str = "ADDITIONAL_ITEM"
STATUS_QUANTITY_DIFFERENCE: str = "QUANTITY_DIFFERENCE"
STATUS_PRICE_DIFFERENCE: str = "PRICE_DIFFERENCE"
STATUS_AMOUNT_DIFFERENCE: str = "AMOUNT_DIFFERENCE"
STATUS_QUANTITY_AND_AMOUNT_DIFFERENCE: str = "QUANTITY_AND_AMOUNT_DIFFERENCE"
STATUS_CREDIT: str = "CREDIT"
STATUS_REVERSAL: str = "REVERSAL"
STATUS_FUZZY_MATCH_REVIEW: str = "FUZZY_MATCH_REVIEW"
STATUS_MASTER_DATA_EXCEPTION: str = "MASTER_DATA_EXCEPTION"
STATUS_DUPLICATE_KEY: str = "DUPLICATE_KEY"
STATUS_DATA_QUALITY_EXCEPTION: str = "DATA_QUALITY_EXCEPTION"
STATUS_UNRESOLVED: str = "UNRESOLVED"

RECONCILIATION_STATUSES: tuple[str, ...] = (
    STATUS_MATCHED,
    STATUS_MATCHED_WITH_SUBSTITUTE,
    STATUS_MISSING_IN_SOURCE_A,
    STATUS_MISSING_IN_SOURCE_B,
    STATUS_ADDITIONAL_TRANSACTION,
    STATUS_ADDITIONAL_ITEM,
    STATUS_QUANTITY_DIFFERENCE,
    STATUS_PRICE_DIFFERENCE,
    STATUS_AMOUNT_DIFFERENCE,
    STATUS_QUANTITY_AND_AMOUNT_DIFFERENCE,
    STATUS_CREDIT,
    STATUS_REVERSAL,
    STATUS_FUZZY_MATCH_REVIEW,
    STATUS_MASTER_DATA_EXCEPTION,
    STATUS_DUPLICATE_KEY,
    STATUS_DATA_QUALITY_EXCEPTION,
    STATUS_UNRESOLVED,
)

# Statuses that represent an exception rather than a clean reconciliation.
EXCEPTION_STATUSES: frozenset[str] = frozenset(
    {
        STATUS_MISSING_IN_SOURCE_A,
        STATUS_MISSING_IN_SOURCE_B,
        STATUS_ADDITIONAL_TRANSACTION,
        STATUS_ADDITIONAL_ITEM,
        STATUS_QUANTITY_DIFFERENCE,
        STATUS_PRICE_DIFFERENCE,
        STATUS_AMOUNT_DIFFERENCE,
        STATUS_QUANTITY_AND_AMOUNT_DIFFERENCE,
        STATUS_FUZZY_MATCH_REVIEW,
        STATUS_MASTER_DATA_EXCEPTION,
        STATUS_DUPLICATE_KEY,
        STATUS_DATA_QUALITY_EXCEPTION,
        STATUS_UNRESOLVED,
    }
)

# ---------------------------------------------------------------------------
# Component statuses (identity / quantity / price / amount)
# ---------------------------------------------------------------------------

IDENTITY_MATCHED: str = "IDENTITY_MATCHED"
IDENTITY_SUBSTITUTE: str = "IDENTITY_SUBSTITUTE"
IDENTITY_UNMATCHED: str = "IDENTITY_UNMATCHED"
IDENTITY_MISSING_A: str = "IDENTITY_MISSING_IN_SOURCE_A"
IDENTITY_MISSING_B: str = "IDENTITY_MISSING_IN_SOURCE_B"
IDENTITY_BLOCKED: str = "IDENTITY_BLOCKED_BY_DATA_QUALITY"

QUANTITY_MATCHED: str = "QUANTITY_MATCHED"
QUANTITY_SHORTAGE: str = "QUANTITY_SHORTAGE"
QUANTITY_EXCESS: str = "QUANTITY_EXCESS"
QUANTITY_NOT_APPLICABLE: str = "QUANTITY_NOT_APPLICABLE"
QUANTITY_INVALID: str = "QUANTITY_INVALID"

PRICE_MATCHED: str = "PRICE_MATCHED"
PRICE_VARIANCE: str = "PRICE_VARIANCE"
PRICE_NOT_APPLICABLE: str = "PRICE_NOT_APPLICABLE"
PRICE_INVALID: str = "PRICE_INVALID"

AMOUNT_MATCHED: str = "AMOUNT_MATCHED"
AMOUNT_VARIANCE: str = "AMOUNT_VARIANCE"
AMOUNT_NOT_APPLICABLE: str = "AMOUNT_NOT_APPLICABLE"
AMOUNT_INVALID: str = "AMOUNT_INVALID"

# ---------------------------------------------------------------------------
# Transaction types
# ---------------------------------------------------------------------------

TXN_SALE: str = "SALE"
TXN_CREDIT: str = "CREDIT"
TXN_REVERSAL: str = "REVERSAL"

TRANSACTION_TYPES: tuple[str, ...] = (TXN_SALE, TXN_CREDIT, TXN_REVERSAL)

# ---------------------------------------------------------------------------
# Data quality
# ---------------------------------------------------------------------------

DQ_ERROR: str = "ERROR"
DQ_WARNING: str = "WARNING"
DQ_BUSINESS_ANOMALY: str = "BUSINESS_ANOMALY"

DQ_SEVERITIES: tuple[str, ...] = (DQ_ERROR, DQ_WARNING, DQ_BUSINESS_ANOMALY)

# ---------------------------------------------------------------------------
# Anomaly detection
# ---------------------------------------------------------------------------

SEVERITY_LOW: str = "LOW"
SEVERITY_MEDIUM: str = "MEDIUM"
SEVERITY_HIGH: str = "HIGH"
SEVERITY_CRITICAL: str = "CRITICAL"

ANOMALY_SEVERITIES: tuple[str, ...] = (
    SEVERITY_LOW,
    SEVERITY_MEDIUM,
    SEVERITY_HIGH,
    SEVERITY_CRITICAL,
)

# Multipliers of the population mean / quantile used by anomaly rules.
ANOMALY_HIGH_AMOUNT_MULTIPLIER: float = 5.0
ANOMALY_HIGH_QUANTITY_MULTIPLIER: float = 5.0
ANOMALY_PRICE_OUTLIER_MULTIPLIER: float = 3.0
ANOMALY_HIGH_RATE_THRESHOLD: float = 0.25
ANOMALY_LOW_CONFIDENCE_THRESHOLD: float = 75.0
ANOMALY_FREQUENCY_MULTIPLIER: float = 3.0

# ---------------------------------------------------------------------------
# Review queue priorities
# ---------------------------------------------------------------------------

PRIORITY_CRITICAL: str = "CRITICAL"
PRIORITY_HIGH: str = "HIGH"
PRIORITY_MEDIUM: str = "MEDIUM"
PRIORITY_LOW: str = "LOW"

# ---------------------------------------------------------------------------
# Scenario catalogue used by the synthetic generator
# ---------------------------------------------------------------------------

SCENARIO_TYPES: tuple[str, ...] = (
    "CLEAN_EXACT_MATCH",
    "PRIMARY_ID_MATCH",
    "BARCODE_MATCH",
    "PRODUCT_CODE_MATCH",
    "NORMALIZED_NAME_MATCH",
    "FUZZY_NAME_MATCH",
    "GENERIC_STRENGTH_EQUIVALENT",
    "POSSIBLE_SUBSTITUTE",
    "MISSING_IN_SOURCE_A",
    "MISSING_IN_SOURCE_B",
    "ADDITIONAL_TRANSACTION",
    "ADDITIONAL_ITEM",
    "QUANTITY_SHORTAGE",
    "QUANTITY_EXCESS",
    "PRICE_DIFFERENCE",
    "AMOUNT_DIFFERENCE",
    "QUANTITY_AND_AMOUNT_DIFFERENCE",
    "CREDIT",
    "REVERSAL",
    "DUPLICATE_TRANSACTION_KEY",
    "DUPLICATE_LINE",
    "MISSING_MASTER_RECORD",
    "MALFORMED_IDENTIFIER",
    "INVALID_NUMERIC",
    "ABNORMAL_REFERENCE_PRICE",
    "HIGH_VALUE_OUTLIER",
    "LOW_CONFIDENCE_FUZZY",
    "UNRESOLVED",
)

# How many of each deliberately injected scenario the generator should build.
SCENARIO_COUNTS: dict[str, int] = {
    "CLEAN_EXACT_MATCH": 900,
    "PRIMARY_ID_MATCH": 120,
    "BARCODE_MATCH": 110,
    "PRODUCT_CODE_MATCH": 110,
    "NORMALIZED_NAME_MATCH": 90,
    "FUZZY_NAME_MATCH": 70,
    "GENERIC_STRENGTH_EQUIVALENT": 70,
    "POSSIBLE_SUBSTITUTE": 45,
    "MISSING_IN_SOURCE_A": 60,
    "MISSING_IN_SOURCE_B": 60,
    "ADDITIONAL_TRANSACTION": 40,
    "ADDITIONAL_ITEM": 55,
    "QUANTITY_SHORTAGE": 55,
    "QUANTITY_EXCESS": 55,
    "PRICE_DIFFERENCE": 50,
    "AMOUNT_DIFFERENCE": 50,
    "QUANTITY_AND_AMOUNT_DIFFERENCE": 40,
    "CREDIT": 45,
    "REVERSAL": 35,
    "DUPLICATE_TRANSACTION_KEY": 20,
    "DUPLICATE_LINE": 25,
    "MISSING_MASTER_RECORD": 30,
    "MALFORMED_IDENTIFIER": 25,
    "INVALID_NUMERIC": 25,
    "ABNORMAL_REFERENCE_PRICE": 8,
    "HIGH_VALUE_OUTLIER": 12,
    "LOW_CONFIDENCE_FUZZY": 30,
    "UNRESOLVED": 25,
}

# ---------------------------------------------------------------------------
# Output file names
# ---------------------------------------------------------------------------

FILE_PRODUCT_MASTER: str = "product_master.csv"
FILE_BRANCH_MASTER: str = "branch_master.csv"
FILE_EMPLOYEE_MASTER: str = "employee_master.csv"
FILE_SOURCE_A_HEADERS: str = "source_a_transaction_headers.csv"
FILE_SOURCE_A_LINES: str = "source_a_transaction_lines.csv"
FILE_SOURCE_B_HEADERS: str = "source_b_transaction_headers.csv"
FILE_SOURCE_B_LINES: str = "source_b_transaction_lines.csv"
FILE_EXPECTED_SCENARIOS: str = "expected_scenarios.csv"

FILE_RECONCILIATION_RESULTS: str = "reconciliation_results.csv"
FILE_DATA_QUALITY: str = "data_quality_issues.csv"
FILE_ANOMALIES: str = "anomaly_results.csv"
FILE_REVIEW_QUEUE: str = "review_queue.csv"
FILE_KPI_SUMMARY: str = "kpi_summary.csv"
FILE_KPI_BY_BRANCH: str = "kpi_by_branch.csv"
FILE_KPI_BY_MONTH: str = "kpi_by_month.csv"
FILE_DASHBOARD_DATA: str = "dashboard_data.json"
FILE_GENERATION_MANIFEST: str = "generation_manifest.json"
