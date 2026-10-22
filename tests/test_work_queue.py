"""Unit tests for Work Queue, Vendor Directory, and Financial Operations."""

from __future__ import annotations

import pytest

from src.database.repository import InvoiceRepository
from src.validator.duplicate_detector import DuplicateDetector
from src.exporter.excel_exporter import export_duplicates_to_csv, export_exceptions_to_csv


@pytest.fixture
def temp_repo(tmp_path):
    db_file = tmp_path / "test_ops.db"
    return InvoiceRepository(db_path=db_file)


def test_work_queue_categorization(temp_repo):
    # 1. Normal valid invoice
    temp_repo.save_invoice({
        "vendor_name": "Reliable Vendor Inc",
        "invoice_number": "INV-100",
        "invoice_date": "2026-10-01",
        "total_amount": 100.0,
        "subtotal": 100.0,
        "validation_status": "VALIDATED",
        "processing_status": "VALIDATED",
    })

    # 2. Missing info invoice
    temp_repo.save_invoice({
        "vendor_name": "Unknown Vendor",
        "invoice_number": "N/A",
        "invoice_date": None,
        "total_amount": 0.0,
        "subtotal": 0.0,
        "validation_status": "NEEDS_REVIEW",
    })

    # 3. Discrepancy invoice
    temp_repo.save_invoice({
        "vendor_name": "Audit Risk LLC",
        "invoice_number": "INV-DISC",
        "invoice_date": "2026-10-02",
        "total_amount": 500.0,
        "subtotal": 200.0,
        "validation_status": "DISCREPANCY",
    })

    queue_all = temp_repo.get_work_queue()
    assert len(queue_all) >= 2

    missing_items = temp_repo.get_work_queue("MISSING_INFO")
    assert any(item["vendor_name"] == "Unknown Vendor" for item in missing_items)

    val_failed = temp_repo.get_work_queue("VALIDATION_FAILED")
    assert any(item["invoice_number"] == "INV-DISC" for item in val_failed)


def test_vendor_directory_and_rename(temp_repo):
    temp_repo.save_invoice({
        "vendor_name": "Old Vendor Co",
        "invoice_number": "INV-1",
        "invoice_date": "2026-10-01",
        "total_amount": 250.0,
        "currency": "USD",
    })
    temp_repo.save_invoice({
        "vendor_name": "Old Vendor Co",
        "invoice_number": "INV-2",
        "invoice_date": "2026-10-05",
        "total_amount": 350.0,
        "currency": "USD",
    })

    vendors = temp_repo.get_vendors_directory()
    assert len(vendors) == 1
    assert vendors[0]["vendor_name"] == "Old Vendor Co"
    assert vendors[0]["total_invoices"] == 2
    assert vendors[0]["currencies"]["USD"] == 600.0

    # Rename vendor safely
    updated = temp_repo.rename_vendor("Old Vendor Co", "New Global Supplies")
    assert updated == 2

    updated_vendors = temp_repo.get_vendors_directory()
    assert updated_vendors[0]["vendor_name"] == "New Global Supplies"


def test_find_duplicate_pairs_and_record_decision(temp_repo):
    inv1_id = temp_repo.save_invoice({
        "vendor_name": "Duplicate Inc",
        "invoice_number": "INV-DUP-1",
        "invoice_date": "2026-10-10",
        "total_amount": 1000.0,
    })
    inv2_id = temp_repo.save_invoice({
        "vendor_name": "Duplicate Inc LLC",
        "invoice_number": "INV-DUP-1",
        "invoice_date": "2026-10-10",
        "total_amount": 1000.0,
    })

    invoices = temp_repo.get_invoices()
    pairs = DuplicateDetector.find_all_duplicate_pairs(invoices)
    assert len(pairs) >= 1
    assert pairs[0]["match_type"] == "EXACT"

    # Record decision
    success = temp_repo.update_duplicate_decision(inv2_id, "CONFIRMED_DUPLICATE", "Matches inv 1")
    assert success is True

    record = temp_repo.get_invoice_by_id(inv2_id)
    assert record["duplicate_decision"] == "CONFIRMED_DUPLICATE"
    assert record["is_duplicate"] == 1


def test_export_exceptions_and_duplicates_csv():
    dummy_exceptions = [{
        "invoice_id": 1,
        "invoice_ref": "INV-01",
        "rule_id": "RULE_TEST",
        "field": "vendor_name",
        "severity": "CRITICAL",
        "current_value": "Unknown",
        "explanation": "Test explanation",
        "suggested_action": "Fix vendor",
    }]
    csv_out = export_exceptions_to_csv(dummy_exceptions)
    assert "RULE_TEST" in csv_out
    assert "Fix vendor" in csv_out

    dummy_pairs = [{
        "invoice_a": {"id": 1, "invoice_number": "INV-1", "vendor_name": "Vendor A"},
        "invoice_b": {"id": 2, "invoice_number": "INV-1", "vendor_name": "Vendor A"},
        "match_type": "EXACT",
        "decision": "UNREVIEWED",
        "explanation": "Identical invoice",
    }]
    dup_csv = export_duplicates_to_csv(dummy_pairs)
    assert "EXACT" in dup_csv
    assert "Vendor A" in dup_csv
