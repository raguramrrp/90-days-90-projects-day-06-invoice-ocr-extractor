"""Unit tests for Field Extractor and Regular Expression Rules."""

from __future__ import annotations

import pytest

from src.parser.extractor import FieldExtractor
from src.parser.nlp_helpers import clean_amount, extract_vendor_heuristic, parse_date_to_iso


def test_clean_amount():
    amt, curr = clean_amount("$1,250.50")
    assert amt == 1250.50
    assert curr == "USD"

    amt_eur, curr_eur = clean_amount("€ 450.00")
    assert amt_eur == 450.00
    assert curr_eur == "EUR"

    amt_inr, curr_inr = clean_amount("₹ 15,000.00")
    assert amt_inr == 15000.00
    assert curr_inr == "INR"


def test_parse_date_to_iso():
    assert parse_date_to_iso("2026-10-22") == "2026-10-22"
    assert parse_date_to_iso("22/10/2026") == "2026-10-22"
    assert parse_date_to_iso("October 15, 2026") == "2026-10-15"
    assert parse_date_to_iso("18-Oct-2026") == "2026-10-18"
    assert parse_date_to_iso("invalid date string") is None


def test_extract_vendor_heuristic():
    sample_lines = [
        "CloudScale Technologies Inc.",
        "742 Evergreen Blvd, Seattle, WA",
        "BILL TO:",
        "Client Corp",
    ]
    vendor, conf = extract_vendor_heuristic(sample_lines)
    assert vendor == "CloudScale Technologies Inc"
    assert conf >= 0.7


def test_field_extractor_full_document():
    raw_doc = """
    Apex Hardware Labs LLC
    104 Technology Drive, Suite 400
    TAX INVOICE

    Invoice No: INV-2026-881
    Invoice Date: 2026-10-15
    Due Date: 2026-11-15
    PO Number: PO-44102
    Terms: Net 30

    BILL TO:
    Robotics Lab Corp

    Description Qty Unit Price Total Amount
    Dell 27 Monitor 2 $400.00 $800.00
    Mechanical Keyboard 1 $150.00 $150.00

    Subtotal: $950.00
    Shipping & Handling: $20.00
    Tax (VAT/GST): $76.00
    Total Amount Due: $1,046.00
    """

    res = FieldExtractor.extract_all(raw_doc)

    assert res["vendor_name"] == "Apex Hardware Labs LLC"
    assert res["invoice_number"] == "INV-2026-881"
    assert res["invoice_date"] == "2026-10-15"
    assert res["due_date"] == "2026-11-15"
    assert res["currency"] == "USD"
    assert res["subtotal"] == 950.00
    assert res["shipping_amount"] == 20.00
    assert res["tax_amount"] == 76.00
    assert res["total_amount"] == 1046.00
    assert res["payment_terms"] == "Net 30"
    assert res["po_number"] == "PO-44102"
    assert len(res["line_items"]) == 2
