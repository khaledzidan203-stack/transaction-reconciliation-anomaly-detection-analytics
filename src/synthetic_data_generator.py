"""Deterministic synthetic data generator for the reconciliation analytics portfolio.

Produces fully reproducible CSV files and a ground-truth manifest so that
every pipeline run, test and dashboard always works with identical data.

Design principles
-----------------
* Single random seed (RANDOM_SEED) drives every choice.
* Products, branches and employees use fictional identifiers only.
* 28 controlled scenario types are injected with known ground truth.
* Source A (POS) and Source B (Reference) share overlapping transactions
  with deliberate discrepancies for every reconciliation path.
* All monetary values are rounded via ``round_money`` before writing.
"""

from __future__ import annotations

import random
from datetime import date, timedelta
from typing import Any

import pandas as pd

from .config import (
    AMOUNT_TOLERANCE,
    DATA_DIR,
    EXAMPLE_OUTPUT_DIR,
    FILE_BRANCH_MASTER,
    FILE_EMPLOYEE_MASTER,
    FILE_EXPECTED_SCENARIOS,
    FILE_GENERATION_MANIFEST,
    FILE_PRODUCT_MASTER,
    FILE_SOURCE_A_HEADERS,
    FILE_SOURCE_A_LINES,
    FILE_SOURCE_B_HEADERS,
    FILE_SOURCE_B_LINES,
    FUZZY_ACCEPT_THRESHOLD,
    FUZZY_REVIEW_THRESHOLD,
    MATCH_EXACT_BARCODE,
    MATCH_EXACT_PRIMARY_ID,
    MATCH_EXACT_PRODUCT_CODE,
    MATCH_FUZZY_NAME,
    MATCH_GENERIC_STRENGTH,
    MATCH_NORMALIZED_NAME,
    MATCH_NONE,
    MATCH_POSSIBLE_SUBSTITUTE,
    MONTHS,
    N_BASE_TRANSACTIONS,
    N_BRANCHES,
    N_EMPLOYEES,
    N_PRODUCTS,
    QUANTITY_TOLERANCE,
    RANDOM_SEED,
    REVIEW_CONFIDENCE_FLOOR,
    SAMPLE_DIR,
    SCENARIO_COUNTS,
    SOURCE_A,
    SOURCE_B,
    STATUS_ADDITIONAL_ITEM,
    STATUS_ADDITIONAL_TRANSACTION,
    STATUS_AMOUNT_DIFFERENCE,
    STATUS_CREDIT,
    STATUS_DATA_QUALITY_EXCEPTION,
    STATUS_DUPLICATE_KEY,
    STATUS_FUZZY_MATCH_REVIEW,
    STATUS_MATCHED,
    STATUS_MATCHED_WITH_SUBSTITUTE,
    STATUS_MASTER_DATA_EXCEPTION,
    STATUS_MISSING_IN_SOURCE_A,
    STATUS_MISSING_IN_SOURCE_B,
    STATUS_PRICE_DIFFERENCE,
    STATUS_QUANTITY_AND_AMOUNT_DIFFERENCE,
    STATUS_QUANTITY_DIFFERENCE,
    STATUS_REVERSAL,
    STATUS_UNRESOLVED,
    TXN_CREDIT,
    TXN_REVERSAL,
    TXN_SALE,
    UNIT_PRICE_TOLERANCE,
)
from .normalization import build_ean13, normalize_product_name
from .utils import describe_frame, ensure_dir, round_money, write_csv, write_json

# ---------------------------------------------------------------------------
# Fictional domain data (generic retail / distribution)
# ---------------------------------------------------------------------------

_CATEGORIES: tuple[str, ...] = (
    "Household",
    "Office Supplies",
    "Electronics Accessories",
    "Personal Care",
    "Kitchen",
    "Stationery",
    "Hardware",
    "Beverages",
)

_BRAND_PREFIXES: tuple[str, ...] = (
    "ZENITH",
    "AURORA",
    "NEXUS",
    "PRISM",
    "VERTEX",
    "HELIX",
    "QUANTUM",
    "APEX",
    "SUMMIT",
    "ORBIT",
    "NOVA",
    "COBALT",
    "TITAN",
    "VANGUARD",
    "SPECTRA",
)

_PRODUCT_BASES: dict[str, tuple[str, ...]] = {
    "Household": (
        "All Purpose Cleaner", "Glass Spray", "Dish Liquid", "Laundry Detergent",
        "Fabric Softener", "Surface Wipes", "Air Freshener", "Floor Polish",
    ),
    "Office Supplies": (
        "Ballpoint Pen", "Highlighter Set", "Binder Clip Box", "Stapler",
        "Desk Organizer", "File Folder Pack", "Whiteboard Marker", "Tape Dispenser",
    ),
    "Electronics Accessories": (
        "USB Cable", "Power Adapter", "Phone Case", "Screen Protector",
        "Battery Pack", "Charging Dock", "HDMI Cable", "Mouse Pad",
    ),
    "Personal Care": (
        "Hand Soap", "Shampoo", "Body Wash", "Toothpaste",
        "Deodorant", "Face Cream", "Hair Gel", "Lotion",
    ),
    "Kitchen": (
        "Cutting Board", "Mixing Bowl Set", "Measuring Cup", "Spatula Set",
        "Storage Container", "Kitchen Towel", "Can Opener", "Peeler",
    ),
    "Stationery": (
        "Notebook", "Sketch Pad", "Colored Pencil Set", "Ruler Set",
        "Glue Stick", "Scissors", "Eraser Pack", "Marker Set",
    ),
    "Hardware": (
        "Screwdriver Set", "Wrench Set", "Tape Measure", "Level Tool",
        "Drill Bit Set", "Utility Knife", "Pliers", "Hammer",
    ),
    "Beverages": (
        "Green Tea Box", "Coffee Beans", "Hot Chocolate", "Juice Pack",
        "Sparkling Water", "Energy Drink", "Herbal Infusion", "Mineral Water",
    ),
}

_STRENGTHS: tuple[str, ...] = (
    "250 ML", "500 ML", "750 ML", "1 L", "1.5 L",
    "100 MG", "250 MG", "500 MG",
    "50 G", "100 G", "200 G", "500 G", "1 KG",
    "5 W", "10 W", "15 W", "20 W",
    "1.5 V", "3 V", "9 V",
    "2000 MAH", "5000 MAH", "10000 MAH",
    "30 CM", "45 CM", "60 CM",
    "10 IN", "12 IN",
)

_CITIES: tuple[str, ...] = (
    "Northport", "Eastvale", "Southfield", "Westbrook", "Cedar Hills",
    "Maple Ridge", "Pine Valley", "Oakwood", "Riverside", "Lakeside",
)


# ---------------------------------------------------------------------------
# Master table generators
# ---------------------------------------------------------------------------


def _generate_products(rng: random.Random) -> pd.DataFrame:
    """Generate *N_PRODUCTS* product master records."""
    rows: list[dict[str, str]] = []
    prod_idx = 0
    for cat in _CATEGORIES:
        bases = _PRODUCT_BASES[cat]
        for base in bases:
            for brand in _BRAND_PREFIXES[:3]:
                prod_idx += 1
                if prod_idx > N_PRODUCTS:
                    break
                product_id = f"PRD-{prod_idx:04d}"
                brand_name = brand
                product_code = f"PC-{brand[:3]}{prod_idx:04d}"
                barcode_body = f"200{prod_idx:08d}"
                barcode = build_ean13(barcode_body)
                strength = rng.choice(_STRENGTHS)
                full_name = f"{brand_name} {base} {strength}"
                generic_name = f"{base} {strength}"
                ref_price = round_money(rng.uniform(2.0, 120.0))
                rows.append({
                    "product_id": product_id,
                    "product_code": product_code,
                    "barcode": barcode,
                    "product_name": full_name,
                    "generic_name": generic_name,
                    "brand": brand_name,
                    "category": cat,
                    "strength": strength,
                    "reference_unit_price": str(ref_price),
                })
            if prod_idx > N_PRODUCTS:
                break
        if prod_idx > N_PRODUCTS:
            break

    return pd.DataFrame(rows)


def _generate_branches() -> pd.DataFrame:
    """Generate *N_BRANCHES* branch records."""
    rows: list[dict[str, str]] = []
    for idx, city in enumerate(_CITIES[:N_BRANCHES], start=1):
        branch_id = f"BR-{idx:03d}"
        rows.append({
            "branch_id": branch_id,
            "branch_name": f"{city} Branch",
            "city": city,
            "region": city.split()[0],
        })
    return pd.DataFrame(rows)


def _generate_employees() -> pd.DataFrame:
    """Generate *N_EMPLOYEES* neutral employee records."""
    rows: list[dict[str, str]] = []
    for idx in range(1, N_EMPLOYEES + 1):
        emp_id = f"EMP-{idx:04d}"
        rows.append({
            "employee_id": emp_id,
            "employee_label": f"Employee {idx:04d}",
            "branch_id": f"BR-{((idx - 1) % N_BRANCHES) + 1:03d}",
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Transaction generators
# ---------------------------------------------------------------------------

def _random_date_for_month(rng: random.Random, month_key: str) -> str:
    """Return a random ISO date string within the given YYYY-MM month."""
    year, mo = int(month_key[:4]), int(month_key[5:7])
    day = rng.randint(1, 28)
    return date(year, mo, day).isoformat()


def _next_txn_id(counter: dict[str, int], prefix: str) -> str:
    """Generate a sequential transaction id like TXN-A-000123."""
    counter[prefix] = counter.get(prefix, 0) + 1
    return f"TXN-{prefix}-{counter[prefix]:06d}"


def _next_line_suffix(counter: dict[str, int]) -> str:
    counter["line"] = counter.get("line", 0) + 1
    return f"L{counter['line']:02d}"


def _pick_products(rng: random.Random, products: pd.DataFrame, n: int) -> list[int]:
    """Return *n* random row indices into the products frame."""
    return rng.sample(range(len(products)), min(n, len(products)))


def _build_header(
    txn_id: str, branch_id: str, employee_id: str,
    txn_date: str, txn_type: str, total_amount: str, source: str,
) -> dict[str, str]:
    return {
        "transaction_id": txn_id,
        "branch_id": branch_id,
        "employee_id": employee_id,
        "transaction_date": txn_date,
        "transaction_type": txn_type,
        "total_amount": total_amount,
        "source": source,
    }


def _build_line(
    line_id: str, txn_id: str, product_id: str, product_code: str,
    barcode: str, product_name: str, generic_name: str, quantity: str,
    unit_price: str, amount: str, reference_id: str, source: str,
) -> dict[str, str]:
    return {
        "line_id": line_id,
        "transaction_id": txn_id,
        "product_id": product_id,
        "product_code": product_code,
        "barcode": barcode,
        "product_name": product_name,
        "generic_name": generic_name,
        "quantity": quantity,
        "unit_price": unit_price,
        "amount": amount,
        "reference_id": reference_id,
        "source": source,
    }


# ---------------------------------------------------------------------------
# Scenario injector
# ---------------------------------------------------------------------------

def _inject_scenarios(
    rng: random.Random,
    products: pd.DataFrame,
    branches: pd.DataFrame,
    employees: pd.DataFrame,
    a_headers: list[dict[str, str]],
    a_lines: list[dict[str, str]],
    b_headers: list[dict[str, str]],
    b_lines: list[dict[str, str]],
    ground_truth: list[dict[str, str]],
    txn_counter: dict[str, int],
    line_counter: dict[str, int],
) -> None:
    """Inject all 28 controlled scenario types with known ground truth."""

    prod_rows = products.to_dict("records")
    br_rows = branches.to_dict("records")
    emp_rows = employees.to_dict("records")

    scenario_id = 0

    def _pick_product() -> dict[str, str]:
        return rng.choice(prod_rows)

    def _pick_branch() -> dict[str, str]:
        return rng.choice(br_rows)

    def _pick_employee() -> dict[str, str]:
        return rng.choice(emp_rows)

    def _pick_month() -> str:
        return rng.choice(list(MONTHS))

    def _new_txn(source: str) -> str:
        return _next_txn_id(txn_counter, "A" if source == SOURCE_A else "B")

    def _new_line_id() -> str:
        return _next_line_suffix(line_counter)

    def _add_ground(
        stype: str, a_txn: str | None, b_txn: str | None,
        a_line: str | None, b_line: str | None,
        match_method: str, recon_status: str,
        review: str, notes: str,
    ) -> None:
        nonlocal scenario_id
        scenario_id += 1
        ground_truth.append({
            "scenario_id": f"SCN-{scenario_id:04d}",
            "scenario_type": stype,
            "source_a_transaction_id": a_txn or "",
            "source_b_transaction_id": b_txn or "",
            "source_a_line_id": a_line or "",
            "source_b_line_id": b_line or "",
            "expected_match_method": match_method,
            "expected_reconciliation_status": recon_status,
            "expected_review_required": review,
            "expected_notes": notes,
        })

    # ------------------------------------------------------------------
    # 1. CLEAN_EXACT_MATCH — both sources agree on every field
    # ------------------------------------------------------------------
    for _ in range(SCENARIO_COUNTS["CLEAN_EXACT_MATCH"]):
        p = _pick_product()
        br = _pick_branch()
        emp = _pick_employee()
        mo = _pick_month()
        dt = _random_date_for_month(rng, mo)
        qty = round(rng.uniform(1, 10), 2)
        price = float(p["reference_unit_price"])
        amt = round_money(qty * price)
        a_txn = _new_txn(SOURCE_A)
        b_txn = _new_txn(SOURCE_B)
        lid_a = f"{a_txn}-{_new_line_id()}"
        lid_b = f"{b_txn}-{_new_line_id()}"
        ref_id = b_txn
        a_headers.append(_build_header(a_txn, br["branch_id"], emp["employee_id"], dt, TXN_SALE, str(amt), SOURCE_A))
        b_headers.append(_build_header(b_txn, br["branch_id"], emp["employee_id"], dt, TXN_SALE, str(amt), SOURCE_B))
        line_kw = dict(
            product_id=p["product_id"], product_code=p["product_code"],
            barcode=p["barcode"], product_name=p["product_name"],
            generic_name=p["generic_name"], source=SOURCE_A,
        )
        a_lines.append(_build_line(lid_a, a_txn, quantity=str(qty), unit_price=str(price), amount=str(amt), reference_id=ref_id, **line_kw))
        line_kw_b = dict(line_kw, source=SOURCE_B)
        b_lines.append(_build_line(lid_b, b_txn, quantity=str(qty), unit_price=str(price), amount=str(amt), reference_id=ref_id, **line_kw_b))
        _add_ground("CLEAN_EXACT_MATCH", a_txn, b_txn, lid_a, lid_b, MATCH_EXACT_PRIMARY_ID, STATUS_MATCHED, "N", "Exact match on all fields")

    # ------------------------------------------------------------------
    # 2. PRIMARY_ID_MATCH — matched via reference_id / product_id
    # ------------------------------------------------------------------
    for _ in range(SCENARIO_COUNTS["PRIMARY_ID_MATCH"]):
        p = _pick_product()
        br = _pick_branch()
        emp = _pick_employee()
        mo = _pick_month()
        dt = _random_date_for_month(rng, mo)
        qty = round(rng.uniform(1, 10), 2)
        price = float(p["reference_unit_price"])
        amt = round_money(qty * price)
        a_txn = _new_txn(SOURCE_A)
        b_txn = _new_txn(SOURCE_B)
        lid_a = f"{a_txn}-{_new_line_id()}"
        lid_b = f"{b_txn}-{_new_line_id()}"
        ref_id = b_txn
        a_headers.append(_build_header(a_txn, br["branch_id"], emp["employee_id"], dt, TXN_SALE, str(amt), SOURCE_A))
        b_headers.append(_build_header(b_txn, br["branch_id"], emp["employee_id"], dt, TXN_SALE, str(amt), SOURCE_B))
        line_kw = dict(product_id=p["product_id"], product_code=p["product_code"], barcode=p["barcode"], product_name=p["product_name"], generic_name=p["generic_name"])
        a_lines.append(_build_line(lid_a, a_txn, quantity=str(qty), unit_price=str(price), amount=str(amt), reference_id=ref_id, source=SOURCE_A, **line_kw))
        b_lines.append(_build_line(lid_b, b_txn, quantity=str(qty), unit_price=str(price), amount=str(amt), reference_id=ref_id, source=SOURCE_B, **line_kw))
        _add_ground("PRIMARY_ID_MATCH", a_txn, b_txn, lid_a, lid_b, MATCH_EXACT_PRIMARY_ID, STATUS_MATCHED, "N", "Matched via reference_id")

    # ------------------------------------------------------------------
    # 3. BARCODE_MATCH — different product_id, same barcode
    # ------------------------------------------------------------------
    for _ in range(SCENARIO_COUNTS["BARCODE_MATCH"]):
        p = _pick_product()
        br = _pick_branch()
        emp = _pick_employee()
        mo = _pick_month()
        dt = _random_date_for_month(rng, mo)
        qty = round(rng.uniform(1, 10), 2)
        price = float(p["reference_unit_price"])
        amt = round_money(qty * price)
        a_txn = _new_txn(SOURCE_A)
        b_txn = _new_txn(SOURCE_B)
        lid_a = f"{a_txn}-{_new_line_id()}"
        lid_b = f"{b_txn}-{_new_line_id()}"
        # Source A: original product_id; Source B: different product_id, same barcode
        alt_pid = f"PRD-{rng.randint(9001, 9999):04d}"
        a_headers.append(_build_header(a_txn, br["branch_id"], emp["employee_id"], dt, TXN_SALE, str(amt), SOURCE_A))
        b_headers.append(_build_header(b_txn, br["branch_id"], emp["employee_id"], dt, TXN_SALE, str(amt), SOURCE_B))
        a_lines.append(_build_line(lid_a, a_txn, product_id=p["product_id"], product_code=p["product_code"], barcode=p["barcode"], product_name=p["product_name"], generic_name=p["generic_name"], quantity=str(qty), unit_price=str(price), amount=str(amt), reference_id="", source=SOURCE_A))
        b_lines.append(_build_line(lid_b, b_txn, product_id=alt_pid, product_code=p["product_code"], barcode=p["barcode"], product_name=p["product_name"], generic_name=p["generic_name"], quantity=str(qty), unit_price=str(price), amount=str(amt), reference_id="", source=SOURCE_B))
        _add_ground("BARCODE_MATCH", a_txn, b_txn, lid_a, lid_b, MATCH_EXACT_BARCODE, STATUS_MATCHED, "N", "Matched via barcode; product_id differs")

    # ------------------------------------------------------------------
    # 4. PRODUCT_CODE_MATCH — same product_code, different product_id/barcode
    # ------------------------------------------------------------------
    for _ in range(SCENARIO_COUNTS["PRODUCT_CODE_MATCH"]):
        p = _pick_product()
        br = _pick_branch()
        emp = _pick_employee()
        mo = _pick_month()
        dt = _random_date_for_month(rng, mo)
        qty = round(rng.uniform(1, 10), 2)
        price = float(p["reference_unit_price"])
        amt = round_money(qty * price)
        a_txn = _new_txn(SOURCE_A)
        b_txn = _new_txn(SOURCE_B)
        lid_a = f"{a_txn}-{_new_line_id()}"
        lid_b = f"{b_txn}-{_new_line_id()}"
        alt_pid = f"PRD-{rng.randint(8001, 9000):04d}"
        alt_barcode = build_ean13(f"300{rng.randint(10000000, 99999999)}")
        a_headers.append(_build_header(a_txn, br["branch_id"], emp["employee_id"], dt, TXN_SALE, str(amt), SOURCE_A))
        b_headers.append(_build_header(b_txn, br["branch_id"], emp["employee_id"], dt, TXN_SALE, str(amt), SOURCE_B))
        a_lines.append(_build_line(lid_a, a_txn, product_id=p["product_id"], product_code=p["product_code"], barcode=p["barcode"], product_name=p["product_name"], generic_name=p["generic_name"], quantity=str(qty), unit_price=str(price), amount=str(amt), reference_id="", source=SOURCE_A))
        b_lines.append(_build_line(lid_b, b_txn, product_id=alt_pid, product_code=p["product_code"], barcode=alt_barcode, product_name=p["product_name"], generic_name=p["generic_name"], quantity=str(qty), unit_price=str(price), amount=str(amt), reference_id="", source=SOURCE_B))
        _add_ground("PRODUCT_CODE_MATCH", a_txn, b_txn, lid_a, lid_b, MATCH_EXACT_PRODUCT_CODE, STATUS_MATCHED, "N", "Matched via product_code")

    # ------------------------------------------------------------------
    # 5. NORMALIZED_NAME_MATCH — same normalized name, different codes
    # ------------------------------------------------------------------
    for _ in range(SCENARIO_COUNTS["NORMALIZED_NAME_MATCH"]):
        p = _pick_product()
        br = _pick_branch()
        emp = _pick_employee()
        mo = _pick_month()
        dt = _random_date_for_month(rng, mo)
        qty = round(rng.uniform(1, 10), 2)
        price = float(p["reference_unit_price"])
        amt = round_money(qty * price)
        a_txn = _new_txn(SOURCE_A)
        b_txn = _new_txn(SOURCE_B)
        lid_a = f"{a_txn}-{_new_line_id()}"
        lid_b = f"{b_txn}-{_new_line_id()}"
        alt_pid = f"PRD-{rng.randint(7001, 8000):04d}"
        alt_code = f"PC-ALT{rng.randint(1000, 9999)}"
        alt_barcode = build_ean13(f"400{rng.randint(10000000, 99999999)}")
        a_headers.append(_build_header(a_txn, br["branch_id"], emp["employee_id"], dt, TXN_SALE, str(amt), SOURCE_A))
        b_headers.append(_build_header(b_txn, br["branch_id"], emp["employee_id"], dt, TXN_SALE, str(amt), SOURCE_B))
        a_lines.append(_build_line(lid_a, a_txn, product_id=p["product_id"], product_code=p["product_code"], barcode=p["barcode"], product_name=p["product_name"], generic_name=p["generic_name"], quantity=str(qty), unit_price=str(price), amount=str(amt), reference_id="", source=SOURCE_A))
        b_lines.append(_build_line(lid_b, b_txn, product_id=alt_pid, product_code=alt_code, barcode=alt_barcode, product_name=p["product_name"], generic_name=p["generic_name"], quantity=str(qty), unit_price=str(price), amount=str(amt), reference_id="", source=SOURCE_B))
        _add_ground("NORMALIZED_NAME_MATCH", a_txn, b_txn, lid_a, lid_b, MATCH_NORMALIZED_NAME, STATUS_MATCHED, "N", "Matched via normalized product name")

    # ------------------------------------------------------------------
    # 6. FUZZY_NAME_MATCH — slightly different names (above accept threshold)
    # ------------------------------------------------------------------
    for _ in range(SCENARIO_COUNTS["FUZZY_NAME_MATCH"]):
        p = _pick_product()
        br = _pick_branch()
        emp = _pick_employee()
        mo = _pick_month()
        dt = _random_date_for_month(rng, mo)
        qty = round(rng.uniform(1, 10), 2)
        price = float(p["reference_unit_price"])
        amt = round_money(qty * price)
        a_txn = _new_txn(SOURCE_A)
        b_txn = _new_txn(SOURCE_B)
        lid_a = f"{a_txn}-{_new_line_id()}"
        lid_b = f"{b_txn}-{_new_line_id()}"
        # Create a slightly different name for source B
        base_tokens = p["product_name"].split()
        if len(base_tokens) > 2:
            # Swap a middle token with a similar variant
            mid = len(base_tokens) // 2
            base_tokens[mid] = base_tokens[mid] + "X"
        b_name = " ".join(base_tokens)
        alt_pid = f"PRD-{rng.randint(6001, 7000):04d}"
        a_headers.append(_build_header(a_txn, br["branch_id"], emp["employee_id"], dt, TXN_SALE, str(amt), SOURCE_A))
        b_headers.append(_build_header(b_txn, br["branch_id"], emp["employee_id"], dt, TXN_SALE, str(amt), SOURCE_B))
        a_lines.append(_build_line(lid_a, a_txn, product_id=p["product_id"], product_code=p["product_code"], barcode=p["barcode"], product_name=p["product_name"], generic_name=p["generic_name"], quantity=str(qty), unit_price=str(price), amount=str(amt), reference_id="", source=SOURCE_A))
        b_lines.append(_build_line(lid_b, b_txn, product_id=alt_pid, product_code=p["product_code"], barcode=p["barcode"], product_name=b_name, generic_name=p["generic_name"], quantity=str(qty), unit_price=str(price), amount=str(amt), reference_id="", source=SOURCE_B))
        _add_ground("FUZZY_NAME_MATCH", a_txn, b_txn, lid_a, lid_b, MATCH_FUZZY_NAME, STATUS_MATCHED, "N", "Fuzzy name match above accept threshold")

    # ------------------------------------------------------------------
    # 7. GENERIC_STRENGTH_EQUIVALENT — same generic, same strength
    # ------------------------------------------------------------------
    for _ in range(SCENARIO_COUNTS["GENERIC_STRENGTH_EQUIVALENT"]):
        p = _pick_product()
        br = _pick_branch()
        emp = _pick_employee()
        mo = _pick_month()
        dt = _random_date_for_month(rng, mo)
        qty = round(rng.uniform(1, 10), 2)
        price = float(p["reference_unit_price"])
        amt = round_money(qty * price)
        a_txn = _new_txn(SOURCE_A)
        b_txn = _new_txn(SOURCE_B)
        lid_a = f"{a_txn}-{_new_line_id()}"
        lid_b = f"{b_txn}-{_new_line_id()}"
        # Different brand, same generic + strength
        other_brand = rng.choice([b for b in _BRAND_PREFIXES if b != p["brand"]])
        b_name = f"{other_brand} {p['generic_name']}"
        alt_pid = f"PRD-{rng.randint(5001, 6000):04d}"
        a_headers.append(_build_header(a_txn, br["branch_id"], emp["employee_id"], dt, TXN_SALE, str(amt), SOURCE_A))
        b_headers.append(_build_header(b_txn, br["branch_id"], emp["employee_id"], dt, TXN_SALE, str(amt), SOURCE_B))
        a_lines.append(_build_line(lid_a, a_txn, product_id=p["product_id"], product_code=p["product_code"], barcode=p["barcode"], product_name=p["product_name"], generic_name=p["generic_name"], quantity=str(qty), unit_price=str(price), amount=str(amt), reference_id="", source=SOURCE_A))
        b_lines.append(_build_line(lid_b, b_txn, product_id=alt_pid, product_code="", barcode="", product_name=b_name, generic_name=p["generic_name"], quantity=str(qty), unit_price=str(price), amount=str(amt), reference_id="", source=SOURCE_B))
        _add_ground("GENERIC_STRENGTH_EQUIVALENT", a_txn, b_txn, lid_a, lid_b, MATCH_GENERIC_STRENGTH, STATUS_MATCHED_WITH_SUBSTITUTE, "N", "Same generic name and strength, different brand")

    # ------------------------------------------------------------------
    # 8. POSSIBLE_SUBSTITUTE — similar generic, different strength
    # ------------------------------------------------------------------
    for _ in range(SCENARIO_COUNTS["POSSIBLE_SUBSTITUTE"]):
        p = _pick_product()
        br = _pick_branch()
        emp = _pick_employee()
        mo = _pick_month()
        dt = _random_date_for_month(rng, mo)
        qty = round(rng.uniform(1, 10), 2)
        price = float(p["reference_unit_price"])
        amt = round_money(qty * price)
        a_txn = _new_txn(SOURCE_A)
        b_txn = _new_txn(SOURCE_B)
        lid_a = f"{a_txn}-{_new_line_id()}"
        lid_b = f"{b_txn}-{_new_line_id()}"
        other_brand = rng.choice([b for b in _BRAND_PREFIXES if b != p["brand"]])
        alt_strength = rng.choice([s for s in _STRENGTHS if s != p["strength"]])
        b_name = f"{other_brand} {p['generic_name'].rsplit(' ', 1)[0]} {alt_strength}"
        alt_pid = f"PRD-{rng.randint(4001, 5000):04d}"
        a_headers.append(_build_header(a_txn, br["branch_id"], emp["employee_id"], dt, TXN_SALE, str(amt), SOURCE_A))
        b_headers.append(_build_header(b_txn, br["branch_id"], emp["employee_id"], dt, TXN_SALE, str(amt), SOURCE_B))
        a_lines.append(_build_line(lid_a, a_txn, product_id=p["product_id"], product_code=p["product_code"], barcode=p["barcode"], product_name=p["product_name"], generic_name=p["generic_name"], quantity=str(qty), unit_price=str(price), amount=str(amt), reference_id="", source=SOURCE_A))
        b_lines.append(_build_line(lid_b, b_txn, product_id=alt_pid, product_code="", barcode="", product_name=b_name, generic_name=p["generic_name"], quantity=str(qty), unit_price=str(price), amount=str(amt), reference_id="", source=SOURCE_B))
        _add_ground("POSSIBLE_SUBSTITUTE", a_txn, b_txn, lid_a, lid_b, MATCH_POSSIBLE_SUBSTITUTE, STATUS_MATCHED_WITH_SUBSTITUTE, "Y", "Different strength, possible substitute")

    # ------------------------------------------------------------------
    # 9. MISSING_IN_SOURCE_A — only in Source B
    # ------------------------------------------------------------------
    for _ in range(SCENARIO_COUNTS["MISSING_IN_SOURCE_A"]):
        p = _pick_product()
        br = _pick_branch()
        emp = _pick_employee()
        mo = _pick_month()
        dt = _random_date_for_month(rng, mo)
        qty = round(rng.uniform(1, 10), 2)
        price = float(p["reference_unit_price"])
        amt = round_money(qty * price)
        b_txn = _new_txn(SOURCE_B)
        lid_b = f"{b_txn}-{_new_line_id()}"
        b_headers.append(_build_header(b_txn, br["branch_id"], emp["employee_id"], dt, TXN_SALE, str(amt), SOURCE_B))
        b_lines.append(_build_line(lid_b, b_txn, product_id=p["product_id"], product_code=p["product_code"], barcode=p["barcode"], product_name=p["product_name"], generic_name=p["generic_name"], quantity=str(qty), unit_price=str(price), amount=str(amt), reference_id="", source=SOURCE_B))
        _add_ground("MISSING_IN_SOURCE_A", "", b_txn, "", lid_b, MATCH_NONE, STATUS_MISSING_IN_SOURCE_A, "Y", "Transaction exists only in Source B")

    # ------------------------------------------------------------------
    # 10. MISSING_IN_SOURCE_B — only in Source A
    # ------------------------------------------------------------------
    for _ in range(SCENARIO_COUNTS["MISSING_IN_SOURCE_B"]):
        p = _pick_product()
        br = _pick_branch()
        emp = _pick_employee()
        mo = _pick_month()
        dt = _random_date_for_month(rng, mo)
        qty = round(rng.uniform(1, 10), 2)
        price = float(p["reference_unit_price"])
        amt = round_money(qty * price)
        a_txn = _new_txn(SOURCE_A)
        lid_a = f"{a_txn}-{_new_line_id()}"
        a_headers.append(_build_header(a_txn, br["branch_id"], emp["employee_id"], dt, TXN_SALE, str(amt), SOURCE_A))
        a_lines.append(_build_line(lid_a, a_txn, product_id=p["product_id"], product_code=p["product_code"], barcode=p["barcode"], product_name=p["product_name"], generic_name=p["generic_name"], quantity=str(qty), unit_price=str(price), amount=str(amt), reference_id="", source=SOURCE_A))
        _add_ground("MISSING_IN_SOURCE_B", a_txn, "", lid_a, "", MATCH_NONE, STATUS_MISSING_IN_SOURCE_B, "Y", "Transaction exists only in Source A")

    # ------------------------------------------------------------------
    # 11. ADDITIONAL_TRANSACTION — extra whole transaction in Source A
    # ------------------------------------------------------------------
    for _ in range(SCENARIO_COUNTS["ADDITIONAL_TRANSACTION"]):
        p = _pick_product()
        br = _pick_branch()
        emp = _pick_employee()
        mo = _pick_month()
        dt = _random_date_for_month(rng, mo)
        qty = round(rng.uniform(1, 10), 2)
        price = float(p["reference_unit_price"])
        amt = round_money(qty * price)
        a_txn = _new_txn(SOURCE_A)
        lid_a = f"{a_txn}-{_new_line_id()}"
        a_headers.append(_build_header(a_txn, br["branch_id"], emp["employee_id"], dt, TXN_SALE, str(amt), SOURCE_A))
        a_lines.append(_build_line(lid_a, a_txn, product_id=p["product_id"], product_code=p["product_code"], barcode=p["barcode"], product_name=p["product_name"], generic_name=p["generic_name"], quantity=str(qty), unit_price=str(price), amount=str(amt), reference_id="", source=SOURCE_A))
        _add_ground("ADDITIONAL_TRANSACTION", a_txn, "", lid_a, "", MATCH_NONE, STATUS_ADDITIONAL_TRANSACTION, "Y", "Additional transaction in Source A with no counterpart")

    # ------------------------------------------------------------------
    # 12. ADDITIONAL_ITEM — extra line within a matched transaction
    # ------------------------------------------------------------------
    for _ in range(SCENARIO_COUNTS["ADDITIONAL_ITEM"]):
        p1 = _pick_product()
        p2 = _pick_product()
        while p2["product_id"] == p1["product_id"]:
            p2 = _pick_product()
        br = _pick_branch()
        emp = _pick_employee()
        mo = _pick_month()
        dt = _random_date_for_month(rng, mo)
        qty1 = round(rng.uniform(1, 10), 2)
        price1 = float(p1["reference_unit_price"])
        amt1 = round_money(qty1 * price1)
        qty2 = round(rng.uniform(1, 5), 2)
        price2 = float(p2["reference_unit_price"])
        amt2 = round_money(qty2 * price2)
        a_txn = _new_txn(SOURCE_A)
        b_txn = _new_txn(SOURCE_B)
        lid_a1 = f"{a_txn}-{_new_line_id()}"
        lid_a2 = f"{a_txn}-{_new_line_id()}"
        lid_b1 = f"{b_txn}-{_new_line_id()}"
        ref_id = b_txn
        total_a = round_money(amt1 + amt2)
        a_headers.append(_build_header(a_txn, br["branch_id"], emp["employee_id"], dt, TXN_SALE, str(total_a), SOURCE_A))
        b_headers.append(_build_header(b_txn, br["branch_id"], emp["employee_id"], dt, TXN_SALE, str(amt1), SOURCE_B))
        a_lines.append(_build_line(lid_a1, a_txn, product_id=p1["product_id"], product_code=p1["product_code"], barcode=p1["barcode"], product_name=p1["product_name"], generic_name=p1["generic_name"], quantity=str(qty1), unit_price=str(price1), amount=str(amt1), reference_id=ref_id, source=SOURCE_A))
        a_lines.append(_build_line(lid_a2, a_txn, product_id=p2["product_id"], product_code=p2["product_code"], barcode=p2["barcode"], product_name=p2["product_name"], generic_name=p2["generic_name"], quantity=str(qty2), unit_price=str(price2), amount=str(amt2), reference_id="", source=SOURCE_A))
        b_lines.append(_build_line(lid_b1, b_txn, product_id=p1["product_id"], product_code=p1["product_code"], barcode=p1["barcode"], product_name=p1["product_name"], generic_name=p1["generic_name"], quantity=str(qty1), unit_price=str(price1), amount=str(amt1), reference_id=ref_id, source=SOURCE_B))
        _add_ground("ADDITIONAL_ITEM", a_txn, b_txn, lid_a2, "", MATCH_NONE, STATUS_ADDITIONAL_ITEM, "Y", "Extra line in Source A not present in Source B")

    # ------------------------------------------------------------------
    # 13. QUANTITY_SHORTAGE — Source A qty < Source B qty
    # ------------------------------------------------------------------
    for _ in range(SCENARIO_COUNTS["QUANTITY_SHORTAGE"]):
        p = _pick_product()
        br = _pick_branch()
        emp = _pick_employee()
        mo = _pick_month()
        dt = _random_date_for_month(rng, mo)
        qty_b = round(rng.uniform(5, 15), 2)
        qty_a = round(qty_b - rng.uniform(1, 3), 2)
        price = float(p["reference_unit_price"])
        amt_a = round_money(qty_a * price)
        amt_b = round_money(qty_b * price)
        a_txn = _new_txn(SOURCE_A)
        b_txn = _new_txn(SOURCE_B)
        lid_a = f"{a_txn}-{_new_line_id()}"
        lid_b = f"{b_txn}-{_new_line_id()}"
        ref_id = b_txn
        a_headers.append(_build_header(a_txn, br["branch_id"], emp["employee_id"], dt, TXN_SALE, str(amt_a), SOURCE_A))
        b_headers.append(_build_header(b_txn, br["branch_id"], emp["employee_id"], dt, TXN_SALE, str(amt_b), SOURCE_B))
        line_kw = dict(product_id=p["product_id"], product_code=p["product_code"], barcode=p["barcode"], product_name=p["product_name"], generic_name=p["generic_name"], unit_price=str(price), reference_id=ref_id)
        a_lines.append(_build_line(lid_a, a_txn, quantity=str(qty_a), amount=str(amt_a), source=SOURCE_A, **line_kw))
        b_lines.append(_build_line(lid_b, b_txn, quantity=str(qty_b), amount=str(amt_b), source=SOURCE_B, **line_kw))
        _add_ground("QUANTITY_SHORTAGE", a_txn, b_txn, lid_a, lid_b, MATCH_EXACT_PRIMARY_ID, STATUS_QUANTITY_DIFFERENCE, "Y", "Source A quantity less than Source B")

    # ------------------------------------------------------------------
    # 14. QUANTITY_EXCESS — Source A qty > Source B qty
    # ------------------------------------------------------------------
    for _ in range(SCENARIO_COUNTS["QUANTITY_EXCESS"]):
        p = _pick_product()
        br = _pick_branch()
        emp = _pick_employee()
        mo = _pick_month()
        dt = _random_date_for_month(rng, mo)
        qty_a = round(rng.uniform(5, 15), 2)
        qty_b = round(qty_a - rng.uniform(1, 3), 2)
        price = float(p["reference_unit_price"])
        amt_a = round_money(qty_a * price)
        amt_b = round_money(qty_b * price)
        a_txn = _new_txn(SOURCE_A)
        b_txn = _new_txn(SOURCE_B)
        lid_a = f"{a_txn}-{_new_line_id()}"
        lid_b = f"{b_txn}-{_new_line_id()}"
        ref_id = b_txn
        a_headers.append(_build_header(a_txn, br["branch_id"], emp["employee_id"], dt, TXN_SALE, str(amt_a), SOURCE_A))
        b_headers.append(_build_header(b_txn, br["branch_id"], emp["employee_id"], dt, TXN_SALE, str(amt_b), SOURCE_B))
        line_kw = dict(product_id=p["product_id"], product_code=p["product_code"], barcode=p["barcode"], product_name=p["product_name"], generic_name=p["generic_name"], unit_price=str(price), reference_id=ref_id)
        a_lines.append(_build_line(lid_a, a_txn, quantity=str(qty_a), amount=str(amt_a), source=SOURCE_A, **line_kw))
        b_lines.append(_build_line(lid_b, b_txn, quantity=str(qty_b), amount=str(amt_b), source=SOURCE_B, **line_kw))
        _add_ground("QUANTITY_EXCESS", a_txn, b_txn, lid_a, lid_b, MATCH_EXACT_PRIMARY_ID, STATUS_QUANTITY_DIFFERENCE, "Y", "Source A quantity exceeds Source B")

    # ------------------------------------------------------------------
    # 15. PRICE_DIFFERENCE — same product, different unit price
    # ------------------------------------------------------------------
    for _ in range(SCENARIO_COUNTS["PRICE_DIFFERENCE"]):
        p = _pick_product()
        br = _pick_branch()
        emp = _pick_employee()
        mo = _pick_month()
        dt = _random_date_for_month(rng, mo)
        qty = round(rng.uniform(1, 10), 2)
        price_a = float(p["reference_unit_price"])
        price_b = round(price_a + rng.uniform(0.5, 5.0), 2)
        amt_a = round_money(qty * price_a)
        amt_b = round_money(qty * price_b)
        a_txn = _new_txn(SOURCE_A)
        b_txn = _new_txn(SOURCE_B)
        lid_a = f"{a_txn}-{_new_line_id()}"
        lid_b = f"{b_txn}-{_new_line_id()}"
        ref_id = b_txn
        a_headers.append(_build_header(a_txn, br["branch_id"], emp["employee_id"], dt, TXN_SALE, str(amt_a), SOURCE_A))
        b_headers.append(_build_header(b_txn, br["branch_id"], emp["employee_id"], dt, TXN_SALE, str(amt_b), SOURCE_B))
        line_kw = dict(product_id=p["product_id"], product_code=p["product_code"], barcode=p["barcode"], product_name=p["product_name"], generic_name=p["generic_name"], quantity=str(qty), reference_id=ref_id)
        a_lines.append(_build_line(lid_a, a_txn, unit_price=str(price_a), amount=str(amt_a), source=SOURCE_A, **line_kw))
        b_lines.append(_build_line(lid_b, b_txn, unit_price=str(price_b), amount=str(amt_b), source=SOURCE_B, **line_kw))
        _add_ground("PRICE_DIFFERENCE", a_txn, b_txn, lid_a, lid_b, MATCH_EXACT_PRIMARY_ID, STATUS_PRICE_DIFFERENCE, "Y", "Unit price variance between sources")

    # ------------------------------------------------------------------
    # 16. AMOUNT_DIFFERENCE — same qty and price but amount mismatch
    # ------------------------------------------------------------------
    for _ in range(SCENARIO_COUNTS["AMOUNT_DIFFERENCE"]):
        p = _pick_product()
        br = _pick_branch()
        emp = _pick_employee()
        mo = _pick_month()
        dt = _random_date_for_month(rng, mo)
        qty = round(rng.uniform(1, 10), 2)
        price = float(p["reference_unit_price"])
        amt_a = round_money(qty * price)
        amt_b = round_money(amt_a + rng.uniform(1.0, 10.0))
        a_txn = _new_txn(SOURCE_A)
        b_txn = _new_txn(SOURCE_B)
        lid_a = f"{a_txn}-{_new_line_id()}"
        lid_b = f"{b_txn}-{_new_line_id()}"
        ref_id = b_txn
        a_headers.append(_build_header(a_txn, br["branch_id"], emp["employee_id"], dt, TXN_SALE, str(amt_a), SOURCE_A))
        b_headers.append(_build_header(b_txn, br["branch_id"], emp["employee_id"], dt, TXN_SALE, str(amt_b), SOURCE_B))
        line_kw = dict(product_id=p["product_id"], product_code=p["product_code"], barcode=p["barcode"], product_name=p["product_name"], generic_name=p["generic_name"], quantity=str(qty), unit_price=str(price), reference_id=ref_id)
        a_lines.append(_build_line(lid_a, a_txn, amount=str(amt_a), source=SOURCE_A, **line_kw))
        b_lines.append(_build_line(lid_b, b_txn, amount=str(amt_b), source=SOURCE_B, **line_kw))
        _add_ground("AMOUNT_DIFFERENCE", a_txn, b_txn, lid_a, lid_b, MATCH_EXACT_PRIMARY_ID, STATUS_AMOUNT_DIFFERENCE, "Y", "Amount variance between sources")

    # ------------------------------------------------------------------
    # 17. QUANTITY_AND_AMOUNT_DIFFERENCE
    # ------------------------------------------------------------------
    for _ in range(SCENARIO_COUNTS["QUANTITY_AND_AMOUNT_DIFFERENCE"]):
        p = _pick_product()
        br = _pick_branch()
        emp = _pick_employee()
        mo = _pick_month()
        dt = _random_date_for_month(rng, mo)
        qty_a = round(rng.uniform(3, 10), 2)
        qty_b = round(qty_a + rng.uniform(1, 4), 2)
        price_a = float(p["reference_unit_price"])
        price_b = round(price_a + rng.uniform(0.5, 3.0), 2)
        amt_a = round_money(qty_a * price_a)
        amt_b = round_money(qty_b * price_b)
        a_txn = _new_txn(SOURCE_A)
        b_txn = _new_txn(SOURCE_B)
        lid_a = f"{a_txn}-{_new_line_id()}"
        lid_b = f"{b_txn}-{_new_line_id()}"
        ref_id = b_txn
        a_headers.append(_build_header(a_txn, br["branch_id"], emp["employee_id"], dt, TXN_SALE, str(amt_a), SOURCE_A))
        b_headers.append(_build_header(b_txn, br["branch_id"], emp["employee_id"], dt, TXN_SALE, str(amt_b), SOURCE_B))
        line_kw = dict(product_id=p["product_id"], product_code=p["product_code"], barcode=p["barcode"], product_name=p["product_name"], generic_name=p["generic_name"], reference_id=ref_id)
        a_lines.append(_build_line(lid_a, a_txn, quantity=str(qty_a), unit_price=str(price_a), amount=str(amt_a), source=SOURCE_A, **line_kw))
        b_lines.append(_build_line(lid_b, b_txn, quantity=str(qty_b), unit_price=str(price_b), amount=str(amt_b), source=SOURCE_B, **line_kw))
        _add_ground("QUANTITY_AND_AMOUNT_DIFFERENCE", a_txn, b_txn, lid_a, lid_b, MATCH_EXACT_PRIMARY_ID, STATUS_QUANTITY_AND_AMOUNT_DIFFERENCE, "Y", "Both quantity and amount differ")

    # ------------------------------------------------------------------
    # 18. CREDIT — credit transaction type
    # ------------------------------------------------------------------
    for _ in range(SCENARIO_COUNTS["CREDIT"]):
        p = _pick_product()
        br = _pick_branch()
        emp = _pick_employee()
        mo = _pick_month()
        dt = _random_date_for_month(rng, mo)
        qty = round(rng.uniform(1, 5), 2)
        price = float(p["reference_unit_price"])
        amt = round_money(qty * price)
        a_txn = _new_txn(SOURCE_A)
        b_txn = _new_txn(SOURCE_B)
        lid_a = f"{a_txn}-{_new_line_id()}"
        lid_b = f"{b_txn}-{_new_line_id()}"
        ref_id = b_txn
        a_headers.append(_build_header(a_txn, br["branch_id"], emp["employee_id"], dt, TXN_CREDIT, str(amt), SOURCE_A))
        b_headers.append(_build_header(b_txn, br["branch_id"], emp["employee_id"], dt, TXN_CREDIT, str(amt), SOURCE_B))
        line_kw = dict(product_id=p["product_id"], product_code=p["product_code"], barcode=p["barcode"], product_name=p["product_name"], generic_name=p["generic_name"], quantity=str(qty), unit_price=str(price), amount=str(amt), reference_id=ref_id)
        a_lines.append(_build_line(lid_a, a_txn, source=SOURCE_A, **line_kw))
        b_lines.append(_build_line(lid_b, b_txn, source=SOURCE_B, **line_kw))
        _add_ground("CREDIT", a_txn, b_txn, lid_a, lid_b, MATCH_EXACT_PRIMARY_ID, STATUS_CREDIT, "N", "Credit transaction")

    # ------------------------------------------------------------------
    # 19. REVERSAL — reversal transaction type
    # ------------------------------------------------------------------
    for _ in range(SCENARIO_COUNTS["REVERSAL"]):
        p = _pick_product()
        br = _pick_branch()
        emp = _pick_employee()
        mo = _pick_month()
        dt = _random_date_for_month(rng, mo)
        qty = round(rng.uniform(1, 5), 2)
        price = float(p["reference_unit_price"])
        amt = round_money(qty * price)
        a_txn = _new_txn(SOURCE_A)
        b_txn = _new_txn(SOURCE_B)
        lid_a = f"{a_txn}-{_new_line_id()}"
        lid_b = f"{b_txn}-{_new_line_id()}"
        ref_id = b_txn
        a_headers.append(_build_header(a_txn, br["branch_id"], emp["employee_id"], dt, TXN_REVERSAL, str(amt), SOURCE_A))
        b_headers.append(_build_header(b_txn, br["branch_id"], emp["employee_id"], dt, TXN_REVERSAL, str(amt), SOURCE_B))
        line_kw = dict(product_id=p["product_id"], product_code=p["product_code"], barcode=p["barcode"], product_name=p["product_name"], generic_name=p["generic_name"], quantity=str(qty), unit_price=str(price), amount=str(amt), reference_id=ref_id)
        a_lines.append(_build_line(lid_a, a_txn, source=SOURCE_A, **line_kw))
        b_lines.append(_build_line(lid_b, b_txn, source=SOURCE_B, **line_kw))
        _add_ground("REVERSAL", a_txn, b_txn, lid_a, lid_b, MATCH_EXACT_PRIMARY_ID, STATUS_REVERSAL, "N", "Reversal transaction")

    # ------------------------------------------------------------------
    # 20. DUPLICATE_TRANSACTION_KEY — same transaction_id appears twice
    # ------------------------------------------------------------------
    for _ in range(SCENARIO_COUNTS["DUPLICATE_TRANSACTION_KEY"]):
        p = _pick_product()
        br = _pick_branch()
        emp = _pick_employee()
        mo = _pick_month()
        dt = _random_date_for_month(rng, mo)
        qty = round(rng.uniform(1, 10), 2)
        price = float(p["reference_unit_price"])
        amt = round_money(qty * price)
        a_txn = _new_txn(SOURCE_A)
        lid_a1 = f"{a_txn}-L01"
        lid_a2 = f"{a_txn}-L02"
        # Write two headers with the same transaction_id
        a_headers.append(_build_header(a_txn, br["branch_id"], emp["employee_id"], dt, TXN_SALE, str(amt), SOURCE_A))
        a_headers.append(_build_header(a_txn, br["branch_id"], emp["employee_id"], dt, TXN_SALE, str(round_money(amt * 2)), SOURCE_A))
        a_lines.append(_build_line(lid_a1, a_txn, product_id=p["product_id"], product_code=p["product_code"], barcode=p["barcode"], product_name=p["product_name"], generic_name=p["generic_name"], quantity=str(qty), unit_price=str(price), amount=str(amt), reference_id="", source=SOURCE_A))
        a_lines.append(_build_line(lid_a2, a_txn, product_id=p["product_id"], product_code=p["product_code"], barcode=p["barcode"], product_name=p["product_name"], generic_name=p["generic_name"], quantity=str(qty), unit_price=str(price), amount=str(amt), reference_id="", source=SOURCE_A))
        _add_ground("DUPLICATE_TRANSACTION_KEY", a_txn, "", lid_a1, "", MATCH_NONE, STATUS_DUPLICATE_KEY, "Y", "Duplicate transaction_id in Source A")

    # ------------------------------------------------------------------
    # 21. DUPLICATE_LINE — same line_id appears twice in a transaction
    # ------------------------------------------------------------------
    for _ in range(SCENARIO_COUNTS["DUPLICATE_LINE"]):
        p = _pick_product()
        br = _pick_branch()
        emp = _pick_employee()
        mo = _pick_month()
        dt = _random_date_for_month(rng, mo)
        qty = round(rng.uniform(1, 10), 2)
        price = float(p["reference_unit_price"])
        amt = round_money(qty * price)
        a_txn = _new_txn(SOURCE_A)
        dup_lid = f"{a_txn}-L01"
        a_headers.append(_build_header(a_txn, br["branch_id"], emp["employee_id"], dt, TXN_SALE, str(round_money(amt * 2)), SOURCE_A))
        a_lines.append(_build_line(dup_lid, a_txn, product_id=p["product_id"], product_code=p["product_code"], barcode=p["barcode"], product_name=p["product_name"], generic_name=p["generic_name"], quantity=str(qty), unit_price=str(price), amount=str(amt), reference_id="", source=SOURCE_A))
        a_lines.append(_build_line(dup_lid, a_txn, product_id=p["product_id"], product_code=p["product_code"], barcode=p["barcode"], product_name=p["product_name"], generic_name=p["generic_name"], quantity=str(qty), unit_price=str(price), amount=str(amt), reference_id="", source=SOURCE_A))
        _add_ground("DUPLICATE_LINE", a_txn, "", dup_lid, "", MATCH_NONE, STATUS_DUPLICATE_KEY, "Y", "Duplicate line_id in Source A")

    # ------------------------------------------------------------------
    # 22. MISSING_MASTER_RECORD — product not in product_master
    # ------------------------------------------------------------------
    for _ in range(SCENARIO_COUNTS["MISSING_MASTER_RECORD"]):
        p = _pick_product()
        br = _pick_branch()
        emp = _pick_employee()
        mo = _pick_month()
        dt = _random_date_for_month(rng, mo)
        qty = round(rng.uniform(1, 10), 2)
        price = float(p["reference_unit_price"])
        amt = round_money(qty * price)
        a_txn = _new_txn(SOURCE_A)
        lid_a = f"{a_txn}-{_new_line_id()}"
        orphan_pid = f"PRD-ORPH{rng.randint(1000, 9999)}"
        a_headers.append(_build_header(a_txn, br["branch_id"], emp["employee_id"], dt, TXN_SALE, str(amt), SOURCE_A))
        a_lines.append(_build_line(lid_a, a_txn, product_id=orphan_pid, product_code="", barcode="", product_name="Unknown Product", generic_name="Unknown", quantity=str(qty), unit_price=str(price), amount=str(amt), reference_id="", source=SOURCE_A))
        _add_ground("MISSING_MASTER_RECORD", a_txn, "", lid_a, "", MATCH_NONE, STATUS_MASTER_DATA_EXCEPTION, "Y", "Product not found in master data")

    # ------------------------------------------------------------------
    # 23. MALFORMED_IDENTIFIER — corrupted product_id format
    # ------------------------------------------------------------------
    for _ in range(SCENARIO_COUNTS["MALFORMED_IDENTIFIER"]):
        p = _pick_product()
        br = _pick_branch()
        emp = _pick_employee()
        mo = _pick_month()
        dt = _random_date_for_month(rng, mo)
        qty = round(rng.uniform(1, 10), 2)
        price = float(p["reference_unit_price"])
        amt = round_money(qty * price)
        a_txn = _new_txn(SOURCE_A)
        lid_a = f"{a_txn}-{_new_line_id()}"
        bad_pid = f"PRD!{rng.randint(1, 99):02d}#"
        a_headers.append(_build_header(a_txn, br["branch_id"], emp["employee_id"], dt, TXN_SALE, str(amt), SOURCE_A))
        a_lines.append(_build_line(lid_a, a_txn, product_id=bad_pid, product_code=p["product_code"], barcode=p["barcode"], product_name=p["product_name"], generic_name=p["generic_name"], quantity=str(qty), unit_price=str(price), amount=str(amt), reference_id="", source=SOURCE_A))
        _add_ground("MALFORMED_IDENTIFIER", a_txn, "", lid_a, "", MATCH_NONE, STATUS_DATA_QUALITY_EXCEPTION, "Y", "Malformed product_id")

    # ------------------------------------------------------------------
    # 24. INVALID_NUMERIC — non-numeric quantity or price
    # ------------------------------------------------------------------
    for _ in range(SCENARIO_COUNTS["INVALID_NUMERIC"]):
        p = _pick_product()
        br = _pick_branch()
        emp = _pick_employee()
        mo = _pick_month()
        dt = _random_date_for_month(rng, mo)
        a_txn = _new_txn(SOURCE_A)
        lid_a = f"{a_txn}-{_new_line_id()}"
        if rng.random() < 0.5:
            bad_qty, bad_price = "N/A", str(float(p["reference_unit_price"]))
            bad_amt = "N/A"
        else:
            bad_qty = str(round(rng.uniform(1, 10), 2))
            bad_price = "ERR"
            bad_amt = "ERR"
        a_headers.append(_build_header(a_txn, br["branch_id"], emp["employee_id"], dt, TXN_SALE, bad_amt, SOURCE_A))
        a_lines.append(_build_line(lid_a, a_txn, product_id=p["product_id"], product_code=p["product_code"], barcode=p["barcode"], product_name=p["product_name"], generic_name=p["generic_name"], quantity=bad_qty, unit_price=bad_price, amount=bad_amt, reference_id="", source=SOURCE_A))
        _add_ground("INVALID_NUMERIC", a_txn, "", lid_a, "", MATCH_NONE, STATUS_DATA_QUALITY_EXCEPTION, "Y", "Non-numeric value in quantity or price field")

    # ------------------------------------------------------------------
    # 25. ABNORMAL_REFERENCE_PRICE — price far from reference
    # ------------------------------------------------------------------
    for _ in range(SCENARIO_COUNTS["ABNORMAL_REFERENCE_PRICE"]):
        p = _pick_product()
        br = _pick_branch()
        emp = _pick_employee()
        mo = _pick_month()
        dt = _random_date_for_month(rng, mo)
        qty = round(rng.uniform(1, 5), 2)
        ref_price = float(p["reference_unit_price"])
        abnormal_price = round_money(ref_price * rng.choice([0.01, 50.0, 100.0]))
        amt = round_money(qty * abnormal_price)
        a_txn = _new_txn(SOURCE_A)
        b_txn = _new_txn(SOURCE_B)
        lid_a = f"{a_txn}-{_new_line_id()}"
        lid_b = f"{b_txn}-{_new_line_id()}"
        ref_id = b_txn
        a_headers.append(_build_header(a_txn, br["branch_id"], emp["employee_id"], dt, TXN_SALE, str(amt), SOURCE_A))
        b_headers.append(_build_header(b_txn, br["branch_id"], emp["employee_id"], dt, TXN_SALE, str(round_money(qty * ref_price)), SOURCE_B))
        line_kw = dict(product_id=p["product_id"], product_code=p["product_code"], barcode=p["barcode"], product_name=p["product_name"], generic_name=p["generic_name"], quantity=str(qty), reference_id=ref_id)
        a_lines.append(_build_line(lid_a, a_txn, unit_price=str(abnormal_price), amount=str(amt), source=SOURCE_A, **line_kw))
        b_lines.append(_build_line(lid_b, b_txn, unit_price=str(ref_price), amount=str(round_money(qty * ref_price)), source=SOURCE_B, **line_kw))
        _add_ground("ABNORMAL_REFERENCE_PRICE", a_txn, b_txn, lid_a, lid_b, MATCH_EXACT_PRIMARY_ID, STATUS_PRICE_DIFFERENCE, "Y", "Unit price far from reference")

    # ------------------------------------------------------------------
    # 26. HIGH_VALUE_OUTLIER — exceptionally large amount
    # ------------------------------------------------------------------
    for _ in range(SCENARIO_COUNTS["HIGH_VALUE_OUTLIER"]):
        p = _pick_product()
        br = _pick_branch()
        emp = _pick_employee()
        mo = _pick_month()
        dt = _random_date_for_month(rng, mo)
        qty = round(rng.uniform(100, 500), 2)
        price = float(p["reference_unit_price"])
        amt = round_money(qty * price)
        a_txn = _new_txn(SOURCE_A)
        b_txn = _new_txn(SOURCE_B)
        lid_a = f"{a_txn}-{_new_line_id()}"
        lid_b = f"{b_txn}-{_new_line_id()}"
        ref_id = b_txn
        a_headers.append(_build_header(a_txn, br["branch_id"], emp["employee_id"], dt, TXN_SALE, str(amt), SOURCE_A))
        b_headers.append(_build_header(b_txn, br["branch_id"], emp["employee_id"], dt, TXN_SALE, str(amt), SOURCE_B))
        line_kw = dict(product_id=p["product_id"], product_code=p["product_code"], barcode=p["barcode"], product_name=p["product_name"], generic_name=p["generic_name"], unit_price=str(price), amount=str(amt), reference_id=ref_id)
        a_lines.append(_build_line(lid_a, a_txn, quantity=str(qty), source=SOURCE_A, **line_kw))
        b_lines.append(_build_line(lid_b, b_txn, quantity=str(qty), source=SOURCE_B, **line_kw))
        _add_ground("HIGH_VALUE_OUTLIER", a_txn, b_txn, lid_a, lid_b, MATCH_EXACT_PRIMARY_ID, STATUS_MATCHED, "N", "High value transaction, matched but flagged for review")

    # ------------------------------------------------------------------
    # 27. LOW_CONFIDENCE_FUZZY — fuzzy score in review band
    # ------------------------------------------------------------------
    for _ in range(SCENARIO_COUNTS["LOW_CONFIDENCE_FUZZY"]):
        p = _pick_product()
        br = _pick_branch()
        emp = _pick_employee()
        mo = _pick_month()
        dt = _random_date_for_month(rng, mo)
        qty = round(rng.uniform(1, 10), 2)
        price = float(p["reference_unit_price"])
        amt = round_money(qty * price)
        a_txn = _new_txn(SOURCE_A)
        b_txn = _new_txn(SOURCE_B)
        lid_a = f"{a_txn}-{_new_line_id()}"
        lid_b = f"{b_txn}-{_new_line_id()}"
        # Create a name that will score in the review band (0.80-0.92)
        base_tokens = p["product_name"].split()
        if len(base_tokens) > 3:
            # Remove one token and alter another
            base_tokens.pop(len(base_tokens) // 2)
            base_tokens[0] = base_tokens[0][:3] + "X"
        b_name = " ".join(base_tokens)
        alt_pid = f"PRD-{rng.randint(3001, 4000):04d}"
        a_headers.append(_build_header(a_txn, br["branch_id"], emp["employee_id"], dt, TXN_SALE, str(amt), SOURCE_A))
        b_headers.append(_build_header(b_txn, br["branch_id"], emp["employee_id"], dt, TXN_SALE, str(amt), SOURCE_B))
        a_lines.append(_build_line(lid_a, a_txn, product_id=p["product_id"], product_code=p["product_code"], barcode=p["barcode"], product_name=p["product_name"], generic_name=p["generic_name"], quantity=str(qty), unit_price=str(price), amount=str(amt), reference_id="", source=SOURCE_A))
        b_lines.append(_build_line(lid_b, b_txn, product_id=alt_pid, product_code="", barcode="", product_name=b_name, generic_name=p["generic_name"], quantity=str(qty), unit_price=str(price), amount=str(amt), reference_id="", source=SOURCE_B))
        _add_ground("LOW_CONFIDENCE_FUZZY", a_txn, b_txn, lid_a, lid_b, MATCH_FUZZY_NAME, STATUS_FUZZY_MATCH_REVIEW, "Y", "Fuzzy match in review band (0.80-0.92)")

    # ------------------------------------------------------------------
    # 28. UNRESOLVED — no match path succeeds
    # ------------------------------------------------------------------
    for _ in range(SCENARIO_COUNTS["UNRESOLVED"]):
        p = _pick_product()
        br = _pick_branch()
        emp = _pick_employee()
        mo = _pick_month()
        dt = _random_date_for_month(rng, mo)
        qty = round(rng.uniform(1, 10), 2)
        price = round_money(rng.uniform(5, 200))
        amt = round_money(qty * price)
        a_txn = _new_txn(SOURCE_A)
        lid_a = f"{a_txn}-{_new_line_id()}"
        orphan_pid = f"PRD-UNR{rng.randint(1000, 9999)}"
        a_headers.append(_build_header(a_txn, br["branch_id"], emp["employee_id"], dt, TXN_SALE, str(amt), SOURCE_A))
        a_lines.append(_build_line(lid_a, a_txn, product_id=orphan_pid, product_code="", barcode="", product_name=f"Unregistered Item {rng.randint(1,999)}", generic_name="Unknown", quantity=str(qty), unit_price=str(price), amount=str(amt), reference_id="", source=SOURCE_A))
        _add_ground("UNRESOLVED", a_txn, "", lid_a, "", MATCH_NONE, STATUS_UNRESOLVED, "Y", "No match path succeeded")

    # Fill remaining base transactions up to N_BASE_TRANSACTIONS
    current_count = len(a_headers) + len(b_headers)
    remaining = max(0, N_BASE_TRANSACTIONS * 2 - current_count)
    for _ in range(remaining // 2):
        p = _pick_product()
        br = _pick_branch()
        emp = _pick_employee()
        mo = _pick_month()
        dt = _random_date_for_month(rng, mo)
        qty = round(rng.uniform(1, 10), 2)
        price = float(p["reference_unit_price"])
        amt = round_money(qty * price)
        a_txn = _new_txn(SOURCE_A)
        b_txn = _new_txn(SOURCE_B)
        lid_a = f"{a_txn}-{_new_line_id()}"
        lid_b = f"{b_txn}-{_new_line_id()}"
        ref_id = b_txn
        a_headers.append(_build_header(a_txn, br["branch_id"], emp["employee_id"], dt, TXN_SALE, str(amt), SOURCE_A))
        b_headers.append(_build_header(b_txn, br["branch_id"], emp["employee_id"], dt, TXN_SALE, str(amt), SOURCE_B))
        line_kw = dict(product_id=p["product_id"], product_code=p["product_code"], barcode=p["barcode"], product_name=p["product_name"], generic_name=p["generic_name"], quantity=str(qty), unit_price=str(price), amount=str(amt))
        a_lines.append(_build_line(lid_a, a_txn, reference_id=ref_id, source=SOURCE_A, **line_kw))
        b_lines.append(_build_line(lid_b, b_txn, reference_id=ref_id, source=SOURCE_B, **line_kw))


# ---------------------------------------------------------------------------
# Top-level entry point
# ---------------------------------------------------------------------------


def generate_all(output_dir: Path | None = None) -> dict[str, Any]:
    """Generate all synthetic CSV files and return a manifest.

    Parameters
    ----------
    output_dir:
        Directory to write files into. Defaults to ``SAMPLE_DIR``.

    Returns
    -------
    dict
        Generation manifest with file paths, SHA-256 digests and row counts.
    """
    out = output_dir or SAMPLE_DIR
    ensure_dir(out)

    rng = random.Random(RANDOM_SEED)

    # Master tables
    products = _generate_products(rng)
    branches = _generate_branches()
    employees = _generate_employees()

    # Transaction containers
    a_headers: list[dict[str, str]] = []
    a_lines: list[dict[str, str]] = []
    b_headers: list[dict[str, str]] = []
    b_lines: list[dict[str, str]] = []
    ground_truth: list[dict[str, str]] = []

    txn_counter: dict[str, int] = {}
    line_counter: dict[str, int] = {}

    _inject_scenarios(
        rng, products, branches, employees,
        a_headers, a_lines, b_headers, b_lines,
        ground_truth, txn_counter, line_counter,
    )

    # Build DataFrames
    df_a_headers = pd.DataFrame(a_headers) if a_headers else pd.DataFrame()
    df_a_lines = pd.DataFrame(a_lines) if a_lines else pd.DataFrame()
    df_b_headers = pd.DataFrame(b_headers) if b_headers else pd.DataFrame()
    df_b_lines = pd.DataFrame(b_lines) if b_lines else pd.DataFrame()
    df_ground = pd.DataFrame(ground_truth) if ground_truth else pd.DataFrame()

    # Write all files
    files_written: dict[str, str] = {}
    manifest_frames: dict[str, dict[str, Any]] = {}

    for name, frame, fname in [
        ("product_master", products, FILE_PRODUCT_MASTER),
        ("branch_master", branches, FILE_BRANCH_MASTER),
        ("employee_master", employees, FILE_EMPLOYEE_MASTER),
        ("source_a_headers", df_a_headers, FILE_SOURCE_A_HEADERS),
        ("source_a_lines", df_a_lines, FILE_SOURCE_A_LINES),
        ("source_b_headers", df_b_headers, FILE_SOURCE_B_HEADERS),
        ("source_b_lines", df_b_lines, FILE_SOURCE_B_LINES),
        ("expected_scenarios", df_ground, FILE_EXPECTED_SCENARIOS),
    ]:
        path = out / fname
        write_csv(frame, path)
        files_written[name] = str(path)
        manifest_frames[name] = {
            **describe_frame(frame),
            "sha256": file_sha256_static(path),
        }

    manifest: dict[str, Any] = {
        "seed": RANDOM_SEED,
        "generated_at": date.today().isoformat(),
        "files": manifest_frames,
    }

    manifest_path = out / FILE_GENERATION_MANIFEST
    write_json(manifest, manifest_path)
    files_written["generation_manifest"] = str(manifest_path)

    return manifest


def file_sha256_static(path: Path) -> str:
    """SHA-256 without importing from utils (avoids circular ref at module level)."""
    import hashlib
    if not path.exists():
        return ""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65_536), b""):
            digest.update(chunk)
    return digest.hexdigest()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    manifest = generate_all()
    print("Generation complete.")
    for name, info in manifest["files"].items():
        print(f"  {name}: {info['rows']} rows, SHA-256 {info['sha256'][:16]}...")
