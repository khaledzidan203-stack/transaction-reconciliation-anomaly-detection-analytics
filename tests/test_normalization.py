"""Tests for src.normalization: comprehensive coverage of all normalizers."""

import pytest
from src.normalization import (
    build_ean13,
    date_key,
    ean_check_digit,
    is_valid_ean13,
    is_well_formed_identifier,
    normalize_barcode,
    normalize_case,
    normalize_code,
    normalize_date,
    normalize_generic_name,
    normalize_hyphens,
    normalize_identifier,
    normalize_null,
    normalize_product_name,
    normalize_punctuation,
    normalize_slashes,
    normalize_strength,
    normalize_unicode,
    normalize_whitespace,
    parse_amount,
    parse_number,
    parse_price,
    parse_quantity,
    product_name_tokens,
    strip_separators,
    to_float_series,
)


class TestNormalizeUnicode:
    def test_nfc_decomposition(self):
        assert normalize_unicode("café") == "cafe"

    def test_none_returns_empty(self):
        assert normalize_unicode(None) == ""

    def test_empty_string(self):
        assert normalize_unicode("") == ""

    def test_ascii_unchanged(self):
        assert normalize_unicode("HELLO 123") == "HELLO 123"


class TestNormalizeNull:
    def test_null_tokens(self):
        for token in ["n/a", "NA", "null", "None", "-", "--", "?", "unknown"]:
            assert normalize_null(token) == ""

    def test_normal_value_preserved(self):
        assert normalize_null("Hello") == "Hello"


class TestNormalizeWhitespace:
    def test_collapse_spaces(self):
        assert normalize_whitespace("  hello   world  ") == "hello world"

    def test_zero_width_removed(self):
        assert normalize_whitespace("hello\u200bworld") == "hello world"


class TestNormalizePunctuation:
    def test_strip_punctuation(self):
        assert normalize_punctuation("A-B.C") == "A B C"


class TestNormalizeHyphensSlashes:
    def test_unicode_dashes(self):
        assert normalize_hyphens("A\u2013B") == "A-B"

    def test_unicode_slashes(self):
        assert normalize_slashes("A\u2044B") == "A/B"


class TestStripSeparators:
    def test_removes_all(self):
        assert strip_separators("A B-C/D.E") == "ABCDE"


class TestIdentifiers:
    def test_normalize_code(self):
        assert normalize_code("PC-001") == "PC001"

    def test_normalize_barcode_digits_only(self):
        assert normalize_barcode("20012345678901") == "20012345678901"

    def test_normalize_barcode_float(self):
        assert normalize_barcode(1234567890123.0) == "1234567890123"

    def test_normalize_barcode_empty(self):
        assert normalize_barcode("N/A") == ""

    def test_normalize_identifier(self):
        assert normalize_identifier("TXN-A-000123") == "TXNA000123"

    def test_well_formed(self):
        assert is_well_formed_identifier("PRD0001") is True
        assert is_well_formed_identifier("PRD!001") is False
        assert is_well_formed_identifier("") is False


class TestEAN13:
    def test_check_digit(self):
        # 2*1 + 0*3 + 0*1 + ... + 0*3 + 1*3 = 2 + 3 = 5 → (10-5)%10 = 5
        assert ean_check_digit("200000000001") == 5

    def test_build_ean13_length(self):
        result = build_ean13("200000000001")
        assert len(result) == 13

    def test_valid_ean13(self):
        code = build_ean13("200000000001")
        assert is_valid_ean13(code)

    def test_invalid_ean13(self):
        # A barcode where the check digit does not match
        assert is_valid_ean13("1234567890123") is False

    def test_short_barcode(self):
        assert is_valid_ean13("123") is False


class TestNormalizeStrength:
    def test_ml_variants(self):
        assert normalize_strength("750ml") == "750 ML"
        assert normalize_strength("750 ML") == "750 ML"
        assert normalize_strength("750  ml") == "750 ML"

    def test_mg_variants(self):
        assert normalize_strength("500mg") == "500 MG"
        assert normalize_strength("500 MG") == "500 MG"

    def test_kg(self):
        assert normalize_strength("10KG") == "10 KG"

    def test_empty(self):
        assert normalize_strength("") == ""


class TestNormalizeProductName:
    def test_unit_split_equivalence(self):
        """750ML and 750 ML must produce identical keys."""
        assert normalize_product_name("ZENITH Cleaner 750ML") == normalize_product_name("ZENITH Cleaner 750 ML")

    def test_more_unit_splits(self):
        assert normalize_product_name("AURORA Soap 500mg") == normalize_product_name("AURORA Soap 500 mg")
        assert normalize_product_name("NEXUS Cable 1L") == normalize_product_name("NEXUS Cable 1 L")
        assert normalize_product_name("PRISM Battery 10KG") == normalize_product_name("PRISM Battery 10 KG")

    def test_negative_cases_preserved(self):
        """Non-unit glued pairs should NOT be split."""
        assert "A100" in normalize_product_name("Model A100")
        assert "X500" in normalize_product_name("Part X500")

    def test_noise_tokens_removed(self):
        result = normalize_product_name("ZENITH Cleaner pack box")
        assert "PACK" not in result
        assert "BOX" not in result

    def test_case_upper(self):
        assert normalize_product_name("zenith cleaner") == normalize_product_name("ZENITH CLEANER")


class TestNormalizeGenericName:
    def test_sorted_tokens(self):
        result = normalize_generic_name("All Purpose Cleaner")
        tokens = result.split()
        assert tokens == sorted(tokens)


class TestNumericParsing:
    def test_plain_number(self):
        assert parse_number("42.5") == 42.5

    def test_integer(self):
        assert parse_number(10) == 10.0

    def test_none(self):
        assert parse_number(None) is None

    def test_negative_parentheses(self):
        assert parse_number("(100.50)") == -100.50

    def test_currency_symbol(self):
        assert parse_number("$25.99") == 25.99

    def test_comma_thousands(self):
        assert parse_number("1,234.56") == 1234.56

    def test_european_decimal(self):
        assert parse_number("1.234,56") is not None

    def test_invalid_text(self):
        assert parse_number("N/A") is None
        assert parse_number("ERR") is None

    def test_parse_quantity(self):
        assert parse_quantity("5") == 5.0

    def test_parse_price(self):
        assert parse_price("12.99") == 12.99

    def test_parse_amount(self):
        assert parse_amount("100.00") == 100.0


class TestDateKey:
    def test_valid_date(self):
        assert date_key("2026-01-15") == "2026-01"

    def test_invalid_date(self):
        assert date_key("not-a-date") == ""

    def test_empty(self):
        assert date_key("") == ""
