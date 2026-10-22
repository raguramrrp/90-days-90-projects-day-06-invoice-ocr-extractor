"""Unit tests for SQLite Database Repository."""

from __future__ import annotations

import pytest

from src.database.repository import InvoiceRepository


@pytest.fixture
def temp_repo(tmp_path):
    db_file = tmp_path / "test_repo.db"
    return InvoiceRepository(db_path=db_file)


def test_save_and_retrieve_invoice(temp_repo):
    inv_data = {
        "vendor_name": "Test Vendor LLC",
        "invoice_number": "INV-TEST-001",
        "invoice_date": "2026-10-10",
        "due_date": "2026-11-10",
        "currency": "USD",
        "subtotal": 1000.0,
        "tax_amount": 100.0,
        "shipping_amount": 0.0,
        "discount_amount": 0.0,
        "total_amount": 1100.0,
        "payment_terms": "Net 30",
        "po_number": "PO-1234",
        "validation_status": "VALIDATED",
    }
    items = [
        {"description": "Item A", "quantity": 2.0, "unit_price": 250.0, "amount": 500.0},
        {"description": "Item B", "quantity": 1.0, "unit_price": 500.0, "amount": 500.0},
    ]

    inv_id = temp_repo.save_invoice(inv_data, items=items, filename="sample.pdf")
    assert inv_id > 0

    fetched = temp_repo.get_invoice_by_id(inv_id)
    assert fetched is not None
    assert fetched["vendor_name"] == "Test Vendor LLC"
    assert fetched["invoice_number"] == "INV-TEST-001"
    assert fetched["total_amount"] == 1100.0
    assert len(fetched["line_items"]) == 2
    assert fetched["line_items"][0]["description"] == "Item A"


def test_update_invoice(temp_repo):
    inv_id = temp_repo.save_invoice(
        {"vendor_name": "Old Vendor", "total_amount": 100.0},
        items=[{"description": "Old Item", "amount": 100.0}],
    )

    updated = temp_repo.update_invoice(
        inv_id,
        {"vendor_name": "New Vendor", "total_amount": 200.0},
        items=[{"description": "New Item", "quantity": 1.0, "unit_price": 200.0, "amount": 200.0}],
    )
    assert updated is True

    record = temp_repo.get_invoice_by_id(inv_id)
    assert record["vendor_name"] == "New Vendor"
    assert record["total_amount"] == 200.0
    assert len(record["line_items"]) == 1
    assert record["line_items"][0]["description"] == "New Item"


def test_delete_invoice(temp_repo):
    inv_id = temp_repo.save_invoice({"vendor_name": "To Delete", "total_amount": 50.0})
    assert temp_repo.get_invoice_by_id(inv_id) is not None

    deleted = temp_repo.delete_invoice(inv_id)
    assert deleted is True
    assert temp_repo.get_invoice_by_id(inv_id) is None


def test_analytics_summary(temp_repo):
    temp_repo.save_invoice({"vendor_name": "Vendor A", "total_amount": 500.0, "validation_status": "VALIDATED"})
    temp_repo.save_invoice({"vendor_name": "Vendor A", "total_amount": 300.0, "validation_status": "VALIDATED"})
    temp_repo.save_invoice({"vendor_name": "Vendor B", "total_amount": 200.0, "validation_status": "DISCREPANCY"})

    analytics = temp_repo.get_analytics_summary()
    assert analytics["total_invoices"] == 3
    assert analytics["total_spend"] == 1000.0
    assert analytics["avg_amount"] == round(1000.0 / 3, 2)
    assert len(analytics["top_vendors"]) == 2
    assert analytics["top_vendors"][0]["vendor_name"] == "Vendor A"
    assert analytics["top_vendors"][0]["total_spent"] == 800.0
