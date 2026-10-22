"""End-to-End Integration Tests for Invoice OCR Pipeline."""

from __future__ import annotations

import json
from pathlib import Path
import pytest

import config
from src.database.repository import InvoiceRepository
from src.exporter.csv_exporter import export_summary_csv
from src.exporter.json_exporter import export_to_json
from src.ocr.engine import OCREngine
from src.parser.extractor import FieldExtractor
from src.validator.schema_validator import validate_invoice_payload


def test_e2e_sample_invoice_processing(tmp_path):
    sample_file = config.BASE_DIR / "data" / "sample_invoices" / "INV-2026-001_Apex_Hardware.png"
    assert sample_file.is_file(), f"Sample invoice missing: {sample_file}"

    # 1. OCR Engine
    engine = OCREngine()
    ocr_result = engine.process_document(sample_file)
    assert ocr_result["mean_confidence"] > 70.0
    assert len(ocr_result["raw_text"]) > 100
    assert len(ocr_result["word_boxes"]) > 10

    # 2. Field Extraction
    extracted = FieldExtractor.extract_all(ocr_result["raw_text"])
    assert extracted["vendor_name"] == "Apex Hardware Labs LLC"
    assert extracted["invoice_number"] == "INV-2026-001"
    assert extracted["subtotal"] == 1395.00
    assert extracted["tax_amount"] == 111.60
    assert extracted["total_amount"] == 1531.60
    assert len(extracted["line_items"]) == 3

    # 3. Validation
    schema, report = validate_invoice_payload(extracted)
    assert schema.validation_status == "VALIDATED"
    assert report["grade"] == "EXCELLENT"
    assert report["math_audit"]["status"] == "PASSED"
    assert report["math_audit"]["discrepancy"] == 0.0

    # 4. Database Persistence
    db_file = tmp_path / "e2e_invoices.db"
    repo = InvoiceRepository(db_path=db_file)
    inv_id = repo.save_invoice(
        schema.model_dump(),
        items=[i.model_dump() for i in schema.line_items],
        filename=sample_file.name,
    )
    assert inv_id == 1

    stored = repo.get_invoice_by_id(inv_id)
    assert stored["vendor_name"] == "Apex Hardware Labs LLC"
    assert stored["total_amount"] == 1531.60
    assert len(stored["line_items"]) == 3

    # 5. Export
    json_out = export_to_json([stored])
    assert "INV-2026-001" in json_out

    csv_out = export_summary_csv([stored])
    assert "Apex Hardware Labs LLC" in csv_out
