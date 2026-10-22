"""Unit tests for the rules-based Validation & Exception Engine."""

from __future__ import annotations

import pytest

from src.validator.rule_engine import ValidationRuleEngine


def test_rule_missing_vendor_and_invoice_no():
    invoice = {
        "id": 1,
        "vendor_name": "Unknown Vendor",
        "invoice_number": "N/A",
        "invoice_date": "2026-10-15",
        "total_amount": 100.0,
        "subtotal": 100.0,
    }
    findings = ValidationRuleEngine.evaluate_invoice(invoice)
    rule_ids = [f.rule_id for f in findings]
    assert "RULE_MISSING_VENDOR" in rule_ids
    assert "RULE_MISSING_INVOICE_NO" in rule_ids


def test_rule_date_chronology():
    invoice = {
        "id": 2,
        "vendor_name": "Acme Corp",
        "invoice_number": "INV-001",
        "invoice_date": "2026-10-20",
        "due_date": "2026-10-10",  # Prior to issue date
        "total_amount": 250.0,
        "subtotal": 250.0,
    }
    findings = ValidationRuleEngine.evaluate_invoice(invoice)
    chronology_findings = [f for f in findings if f.rule_id == "RULE_DATE_CHRONOLOGY"]
    assert len(chronology_findings) == 1
    assert chronology_findings[0].severity == "WARNING"


def test_rule_math_imbalance():
    invoice = {
        "id": 3,
        "vendor_name": "CloudScale",
        "invoice_number": "INV-999",
        "invoice_date": "2026-10-15",
        "subtotal": 100.0,
        "tax_amount": 10.0,
        "shipping_amount": 5.0,
        "discount_amount": 0.0,
        "total_amount": 150.0,  # Imbalance: 100 + 10 + 5 != 150
    }
    findings = ValidationRuleEngine.evaluate_invoice(invoice)
    imbalance_findings = [f for f in findings if f.rule_id == "RULE_MATH_IMBALANCE"]
    assert len(imbalance_findings) == 1
    assert imbalance_findings[0].severity == "CRITICAL"


def test_rule_line_item_arithmetic():
    invoice = {
        "id": 4,
        "vendor_name": "Apex Hardware",
        "invoice_number": "INV-404",
        "invoice_date": "2026-10-15",
        "subtotal": 200.0,
        "total_amount": 200.0,
        "line_items": [
            {"description": "Monitor", "quantity": 2.0, "unit_price": 50.0, "amount": 200.0}  # 2 * 50 != 200
        ],
    }
    findings = ValidationRuleEngine.evaluate_invoice(invoice)
    item_math = [f for f in findings if f.rule_id == "RULE_LINE_ITEM_ARITHMETIC"]
    assert len(item_math) == 1
    assert "stated: $200.00" in item_math[0].current_value.lower()
