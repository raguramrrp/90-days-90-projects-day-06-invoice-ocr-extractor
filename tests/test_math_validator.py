"""Unit tests for Accounting Math Reconciliation Validator."""

from __future__ import annotations

import pytest

from src.validator.math_validator import MathValidator
from src.validator.schema_validator import validate_invoice_payload


def test_math_validator_exact_match():
    line_items = [
        {"description": "Item 1", "quantity": 2.0, "unit_price": 50.0, "amount": 100.0},
        {"description": "Item 2", "quantity": 1.0, "unit_price": 200.0, "amount": 200.0},
    ]
    # Subtotal 300, Tax 30, Shipping 10, Discount 20 -> Total 320
    res = MathValidator.validate_totals(
        subtotal=300.0,
        tax_amount=30.0,
        shipping_amount=10.0,
        discount_amount=20.0,
        total_amount=320.0,
        line_items=line_items,
    )
    assert res["status"] == "PASSED"
    assert res["is_valid"] is True
    assert res["discrepancy"] == 0.0
    assert res["line_items_match"] is True


def test_math_validator_discrepancy():
    line_items = [
        {"description": "Item 1", "quantity": 1.0, "unit_price": 100.0, "amount": 100.0},
    ]
    # Subtotal 100, Tax 10 -> Total should be 110, but extracted total is 150
    res = MathValidator.validate_totals(
        subtotal=100.0,
        tax_amount=10.0,
        shipping_amount=0.0,
        discount_amount=0.0,
        total_amount=150.0,
        line_items=line_items,
    )
    assert res["status"] == "DISCREPANCY"
    assert res["is_valid"] is False
    assert res["discrepancy"] == 40.0


def test_schema_validator_audit_grade():
    payload = {
        "vendor_name": "Apex Hardware Labs",
        "invoice_number": "INV-100",
        "invoice_date": "2026-10-01",
        "due_date": "2026-10-31",
        "currency": "USD",
        "subtotal": 500.0,
        "tax_amount": 50.0,
        "shipping_amount": 0.0,
        "discount_amount": 0.0,
        "total_amount": 550.0,
        "line_items": [
            {"description": "Server", "quantity": 1.0, "unit_price": 500.0, "amount": 500.0}
        ],
    }

    schema, report = validate_invoice_payload(payload)
    assert schema.validation_status == "VALIDATED"
    assert report["grade"] == "EXCELLENT"
    assert report["math_audit"]["is_valid"] is True
