"""Unit tests for Batch Manager."""

from __future__ import annotations

from pathlib import Path
import pytest

import config
from src.batch.batch_manager import BatchManager
from src.database.repository import InvoiceRepository


@pytest.fixture
def batch_manager(tmp_path):
    repo = InvoiceRepository(db_path=tmp_path / "batch_test.db")
    return BatchManager(repo=repo)


def test_batch_processing_multiple_samples(batch_manager):
    sample_dir = config.BASE_DIR / "data" / "sample_invoices"
    png1 = sample_dir / "INV-2026-001_Apex_Hardware.png"
    png2 = sample_dir / "INV-2026-002_CloudScale_Technologies.png"

    assert png1.is_file()
    assert png2.is_file()

    batch_input = [
        {"name": png1.name, "content": png1},
        {"name": png2.name, "content": png2},
    ]

    report = batch_manager.process_batch(batch_input)
    assert report["total_files"] == 2
    assert report["success_count"] >= 1
    assert len(report["items"]) == 2
    assert report["items"][0]["status"] in ("VALIDATED", "VERIFIED_WITH_WARNINGS")


def test_batch_error_isolation(batch_manager):
    # A corrupted file should NOT fail the batch
    batch_input = [
        {"name": "corrupt.png", "content": b"not a real image"},
        {"name": "empty.pdf", "content": b""},
    ]

    report = batch_manager.process_batch(batch_input)
    assert report["total_files"] == 2
    assert report["failed_count"] == 2
    assert report["items"][0]["status"] == "FAILED"
    assert report["items"][0]["error"] is not None
