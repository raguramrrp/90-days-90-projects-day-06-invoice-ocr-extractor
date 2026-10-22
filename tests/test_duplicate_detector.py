"""Unit tests for Duplicate Invoice Detection."""

from __future__ import annotations

import pytest

from src.validator.duplicate_detector import DuplicateDetector


def test_normalize_vendor():
    assert DuplicateDetector.normalize_vendor("Apex Hardware Labs LLC") == "apexhardwarelabs"
    assert DuplicateDetector.normalize_vendor("CloudScale Technologies Inc.") == "cloudscale"
    assert DuplicateDetector.normalize_vendor("Unknown Vendor") == ""


def test_normalize_invoice_number():
    assert DuplicateDetector.normalize_invoice_number("INV-2026-001") == "INV2026001"
    assert DuplicateDetector.normalize_invoice_number("# 88421") == "88421"
    assert DuplicateDetector.normalize_invoice_number("N/A") == ""


def test_exact_duplicate_detection():
    existing = [
        {
            "id": 1,
            "vendor_name": "Apex Hardware Labs LLC",
            "invoice_number": "INV-2026-001",
            "invoice_date": "2026-10-15",
            "total_amount": 1531.60,
        }
    ]

    candidate = {
        "vendor_name": "Apex Hardware Labs",
        "invoice_number": "inv-2026-001",
        "invoice_date": "2026-10-15",
        "total_amount": 1531.60,
    }

    res = DuplicateDetector.check_duplicate(candidate, existing)
    assert res["is_duplicate"] is True
    assert res["severity"] == "EXACT"
    assert len(res["matching_invoices"]) == 1


def test_suspected_duplicate_detection():
    existing = [
        {
            "id": 2,
            "vendor_name": "CloudScale Technologies",
            "invoice_number": "CS-999",
            "invoice_date": "2026-10-18",
            "total_amount": 1210.00,
        }
    ]

    # Different or missing invoice number, but same vendor, date, and amount
    candidate = {
        "vendor_name": "CloudScale Technologies Inc.",
        "invoice_number": "CS-DIFFERENT",
        "invoice_date": "2026-10-18",
        "total_amount": 1210.00,
    }

    res = DuplicateDetector.check_duplicate(candidate, existing)
    assert res["is_duplicate"] is True
    assert res["severity"] == "SUSPECTED"


def test_no_duplicate():
    existing = [
        {
            "id": 3,
            "vendor_name": "Metro Office Supplies",
            "invoice_number": "INV-100",
            "invoice_date": "2026-10-20",
            "total_amount": 300.00,
        }
    ]

    candidate = {
        "vendor_name": "CyberShield Security",
        "invoice_number": "INV-200",
        "invoice_date": "2026-10-21",
        "total_amount": 500.00,
    }

    res = DuplicateDetector.check_duplicate(candidate, existing)
    assert res["is_duplicate"] is False
    assert res["severity"] == "NONE"
