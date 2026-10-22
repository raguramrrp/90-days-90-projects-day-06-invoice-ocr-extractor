"""Unit tests for JSON and CSV Exporters."""

from __future__ import annotations

import json
import pytest

from src.exporter.csv_exporter import export_detailed_items_csv, export_summary_csv
from src.exporter.json_exporter import export_to_json


@pytest.fixture
def sample_invoices():
    return [
        {
            "id": 1,
            "filename": "inv1.png",
            "vendor_name": "Apex Hardware Labs",
            "invoice_number": "INV-001",
            "invoice_date": "2026-10-15",
            "due_date": "2026-11-15",
            "currency": "USD",
            "subtotal": 1000.0,
            "tax_amount": 80.0,
            "shipping_amount": 20.0,
            "discount_amount": 0.0,
            "total_amount": 1100.0,
            "validation_status": "VALIDATED",
            "line_items": [
                {"description": "Monitor", "quantity": 2.0, "unit_price": 500.0, "amount": 1000.0}
            ],
        }
    ]


def test_export_to_json(sample_invoices):
    json_str = export_to_json(sample_invoices)
    parsed = json.loads(json_str)
    assert isinstance(parsed, list)
    assert len(parsed) == 1
    assert parsed[0]["vendor_name"] == "Apex Hardware Labs"
    assert parsed[0]["invoice_number"] == "INV-001"


def test_export_summary_csv(sample_invoices):
    csv_str = export_summary_csv(sample_invoices)
    lines = csv_str.strip().splitlines()
    assert len(lines) == 2  # Header + 1 row
    assert "Apex Hardware Labs" in lines[1]
    assert "INV-001" in lines[1]
    assert "1100.0" in lines[1]


def test_export_detailed_items_csv(sample_invoices):
    csv_str = export_detailed_items_csv(sample_invoices)
    lines = csv_str.strip().splitlines()
    assert len(lines) == 2  # Header + 1 item row
    assert "Monitor" in lines[1]
    assert "500.0" in lines[1]
