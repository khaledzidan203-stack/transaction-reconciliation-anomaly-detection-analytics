"""Reusable normalization utilities.

Deterministic rules run first in the matching pipeline; fuzzy matching is only
ever attempted on already normalized text. Keeping normalization in one module
means the matching engine, the data quality engine and the tests all share
exactly the same definition of "equal".
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any

import pandas as pd

# Tokens that are treated as missing across every source system.
NULL_TOKENS: frozenset[str] = frozenset(
    {
        "",
        "-",
        "--",
        "n/a",
        "na",
        "nan",
        "none",
        "null",
        "nil",
        "unknown",
        "?",
    }
)

# Unicode dash and separator variants collapsed to a single ASCII hyphen.
_DASH_CHARS = "\u2010\u2011\u2012\u2013\u2014\u2015\u2212\uff0d"
_SLASH_CHARS = "/\\\u2044\u2215\uff0f"

# Noise tokens removed from product names before keying. They carry no
# discriminating power and are a common source of false mismatches.
_NAME_NOISE_TOKENS: frozenset[str] = frozenset(
    {
        "PACK",
        "PACKS",
        "BOX",
        "BOXES",
        "UNIT",
        "UNITS",
        "PIECE",
        "PIECES",
        "PCS",
        "PC",
        "EACH",
        "EA",
        "THE",
        "AND",
        "WITH",
        "OF",
        "FOR",
        "NEW",
    }
)

# Strength unit synonyms normalized to a canonical token.
_STRENGTH_UNITS: dict[str, str] = {
    "mg": "MG",
    "milligram": "MG",
    "milligrams": "MG",
    "g": "G",
    "gm": "G",
    "gram": "G",
    "grams": "G",
    "kg": "KG",
    "kilogram": "KG",
    "kilograms": "KG",
    "ml": "ML",
    "milliliter": "ML",
    "milliliters": "ML",
    "millilitre": "ML",
    "millilitres": "ML",
    "l": "L",
    "liter": "L",
    "liters": "L",
    "litre": "L",
    "litres": "L",
    "iu": "IU",
    "u": "IU",
    "unit": "IU",
    "units": "IU",
    "w": "W",
    "watt": "W",
    "watts": "W",
    "v": "V",
    "volt": "V",
    "volts": "V",
    "a": "A",
    "amp": "A",
    "mah": "MAH",
    "cm": "CM",
    "m": "M",
    "inch": "IN",
    "inches": "IN",
    '"': "IN",
}

_STRENGTH_PATTERN = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*(" + "|".join(sorted(_STRENGTH_UNITS, key=len, reverse=True)) + r")\b",
    re.IGNORECASE,
)

# Splits a glued number and unit ("750ML" -> "750 ML") so that spacing
# differences between source systems do not create false name mismatches.
# Longest units are listed first so that "ML" is not shadowed by "M".
_UNIT_SPLIT_PATTERN = re.compile(
    r"(?<=\d)\s*(?=(?:MAH|ML|MG|KG|CM|IU|IN|G|L|W|V|A|M)\b)"
)


# ---------------------------------------------------------------------------
# Text primitives
# ---------------------------------------------------------------------------


def normalize_unicode(value: Any) -> str:
    """Apply NFKC normalization and drop combining marks."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = unicodedata.normalize("NFKC", str(value))
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def normalize_null(value: Any) -> str:
    """Return an empty string for any value that should be treated as null."""
    text = normalize_unicode(value).strip()
    if text.casefold() in NULL_TOKENS:
        return ""
    return text


def normalize_whitespace(value: Any) -> str:
    """Trim and collapse repeated whitespace, including zero width characters."""
    text = normalize_null(value)
    text = re.sub(r"[\u00a0\u200b\u200c\u200d\u2060\ufeff]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_case(value: Any) -> str:
    """Canonical comparison casing (upper case)."""
    return normalize_whitespace(value).upper()


def normalize_punctuation(value: Any) -> str:
    """Replace punctuation runs with a single space, keeping alphanumerics."""
    text = normalize_case(value)
    return re.sub(r"[^A-Z0-9]+", " ", text).strip()


def normalize_hyphens(value: Any) -> str:
    """Collapse Unicode dash variants to a single ASCII hyphen."""
    text = normalize_whitespace(value)
    for char in _DASH_CHARS:
        text = text.replace(char, "-")
    return text


def normalize_slashes(value: Any) -> str:
    """Collapse slash variants to a single ASCII slash."""
    text = normalize_whitespace(value)
    for char in _SLASH_CHARS:
        text = text.replace(char, "/")
    return text


def strip_separators(value: Any) -> str:
    """Remove spaces, hyphens, slashes and dots (used for identifier keys)."""
    text = normalize_slashes(normalize_hyphens(value))
    return re.sub(r"[\s\-/.]", "", text).upper()


# ---------------------------------------------------------------------------
# Identifier normalization
# ---------------------------------------------------------------------------


def normalize_code(value: Any) -> str:
    """Normalize a product or master code for exact comparison.

    Leading zeros are preserved because they can be significant, but internal
    separators are removed and casing is canonicalized.
    """
    return strip_separators(value)


def normalize_barcode(value: Any) -> str:
    """Normalize a barcode to digits only.

    Returns an empty string when no digits are present so that downstream
    equality checks never compare a blank against a real barcode.
    """
    text = normalize_null(value)
    if isinstance(value, float) and value.is_integer():
        text = str(int(value))
    digits = re.sub(r"\D", "", text)
    return digits


def normalize_identifier(value: Any) -> str:
    """Normalize a transaction, line or reference identifier."""
    return strip_separators(value)


def is_well_formed_identifier(value: Any) -> bool:
    """An identifier is well formed when it is non empty and alphanumeric."""
    text = normalize_identifier(value)
    return bool(text) and text.isalnum()


# ---------------------------------------------------------------------------
# Barcode validation (EAN-13 / UPC-A style check digit)
# ---------------------------------------------------------------------------


def ean_check_digit(digits: str) -> int:
    """Return the GS1 modulo-10 check digit for a string of digits."""
    cleaned = re.sub(r"\D", "", digits)
    if not cleaned:
        return 0
    total = 0
    # Weighting is applied from the right, ignoring the check digit position.
    for index, char in enumerate(reversed(cleaned)):
        weight = 3 if index % 2 == 0 else 1
        total += int(char) * weight
    return (10 - (total % 10)) % 10


def build_ean13(body: str) -> str:
    """Build a valid 13 digit barcode from a 12 digit body."""
    digits = re.sub(r"\D", "", body)[:12].ljust(12, "0")
    return digits + str(ean_check_digit(digits))


def is_valid_ean13(value: Any) -> bool:
    """Return True when the value is a structurally valid 13 digit barcode."""
    digits = normalize_barcode(value)
    if len(digits) != 13:
        return False
    return ean_check_digit(digits[:12]) == int(digits[12])


# ---------------------------------------------------------------------------
# Product name / generic / strength normalization
# ---------------------------------------------------------------------------


def normalize_strength(value: Any) -> str:
    """Canonicalize a strength or specification string.

    ``"750ml"``, ``"750 ML"`` and ``"750  ml"`` all normalize to ``"750 ML"``.
    Multiple strengths are sorted so that ordering differences do not matter.
    """
    text = normalize_whitespace(value)
    if not text:
        return ""
    text = text.replace("\u00b5", "u").replace(",", ".")
    found = _STRENGTH_PATTERN.findall(text)
    if not found:
        return re.sub(r"\s+", " ", normalize_punctuation(text))
    tokens: list[str] = []
    for amount, unit in found:
        canonical_unit = _STRENGTH_UNITS.get(unit.casefold(), unit.upper())
        number = amount.replace(".", "")
        if number.endswith("0") and "." in amount:
            number = amount.rstrip("0").rstrip(".")
        tokens.append(f"{number} {canonical_unit}")
    # Anything in the source that was not recognized as a strength is kept so
    # that free text specifications remain comparable.
    leftover = _STRENGTH_PATTERN.sub(" ", text)
    leftover = re.sub(r"\s+", " ", normalize_punctuation(leftover))
    ordered = sorted(set(tokens))
    if leftover:
        ordered.append(leftover)
    return " ".join(ordered).strip()


def normalize_product_name(value: Any) -> str:
    """Deterministic product name key used by the normalized name matcher.

    The full commercial name is kept (brand included) so that two different
    brands of the same generic product never collapse to the same key. That
    distinction is what separates a deterministic name match from an
    equivalent product match.

    Glued number-unit pairs such as ``"750ML"`` are split to ``"750 ML"`` so
    that spacing differences between source systems never cause a false
    mismatch on the deterministic name path.
    """
    text = normalize_case(value)
    text = normalize_slashes(normalize_hyphens(text))
    text = _UNIT_SPLIT_PATTERN.sub(" ", text)
    text = re.sub(r"[^A-Z0-9. ]+", " ", text)
    tokens = [token for token in text.split() if token and token not in _NAME_NOISE_TOKENS]
    return " ".join(tokens)


def normalize_generic_name(value: Any) -> str:
    """Normalize a generic product type name (brand independent)."""
    text = normalize_punctuation(value)
    tokens = [token for token in text.split() if token and token not in _NAME_NOISE_TOKENS]
    return " ".join(sorted(tokens))


def product_name_tokens(value: Any) -> list[str]:
    """Return the normalized token list of a product name."""
    key = normalize_product_name(value)
    return key.split() if key else []


def brand_token(value: Any) -> str:
    """Return the leading brand token of a product name, if any."""
    tokens = product_name_tokens(value)
    return tokens[0] if tokens else ""


# ---------------------------------------------------------------------------
# Numeric parsing
# ---------------------------------------------------------------------------

_CURRENCY_NOISE = re.compile(r"[^\d.,\-+eE]")


def parse_number(value: Any) -> float | None:
    """Parse a numeric value from text, returning None when impossible.

    Handles thousand separators, currency symbols, parenthesised negatives and
    Excel style text numbers. Returns ``None`` (not ``0``) when the value is
    genuinely unparseable so that data quality checks can flag it.
    """
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        number = float(value)
        return number if number == number else None  # NaN check without math
    text = normalize_whitespace(value)
    if not text or text.casefold() in NULL_TOKENS:
        return None
    negative_parentheses = text.startswith("(") and text.endswith(")")
    cleaned = _CURRENCY_NOISE.sub("", text)
    if not cleaned or cleaned in {"-", "+", "."}:
        return None
    if "," in cleaned and "." in cleaned:
        # Assume the right most separator is the decimal point.
        if cleaned.rfind(",") > cleaned.rfind("."):
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    elif "," in cleaned:
        cleaned = cleaned.replace(",", ".") if cleaned.count(",") == 1 else cleaned.replace(",", "")
    try:
        number = float(cleaned)
    except ValueError:
        return None
    if number != number:  # NaN
        return None
    return -number if negative_parentheses else number


def parse_quantity(value: Any) -> float | None:
    """Parse a quantity, rejecting non numeric input."""
    return parse_number(value)


def parse_price(value: Any) -> float | None:
    """Parse a unit price."""
    return parse_number(value)


def parse_amount(value: Any) -> float | None:
    """Parse a monetary amount."""
    return parse_number(value)


def to_float_series(series: pd.Series, parser: Any = parse_number) -> pd.Series:
    """Apply a parser across a Series, yielding float or ``pd.NA``."""
    parsed = series.map(parser)
    return pd.to_numeric(parsed, errors="coerce").astype("float64")


# ---------------------------------------------------------------------------
# Date handling
# ---------------------------------------------------------------------------


def normalize_date(value: Any) -> pd.Timestamp | None:
    """Parse a date string into a timestamp, or None when invalid."""
    text = normalize_whitespace(value)
    if not text:
        return None
    try:
        parsed = pd.to_datetime(text, errors="raise", format="mixed")
    except (ValueError, TypeError):
        return None
    if pd.isna(parsed):
        return None
    return parsed


def date_key(value: Any) -> str:
    """Return an ISO ``YYYY-MM`` month key for trend analysis."""
    parsed = normalize_date(value)
    return "" if parsed is None else parsed.strftime("%Y-%m")
