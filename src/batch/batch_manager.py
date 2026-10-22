"""Batch Processing Center for Multiple Invoices.

Orchestrates multi-file document queues, processes documents independently,
manages error isolation, and persists batch execution summaries.
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Callable, Dict, List, Optional

from src.database.repository import InvoiceRepository
from src.ocr.engine import OCREngine
from src.parser.extractor import FieldExtractor
from src.validator.duplicate_detector import DuplicateDetector
from src.validator.schema_validator import validate_invoice_payload


class BatchManager:
    """Manages batch ingestion and independent document execution."""

    def __init__(self, repo: Optional[InvoiceRepository] = None, engine: Optional[OCREngine] = None):
        self.repo = repo or InvoiceRepository()
        self.engine = engine or OCREngine()

    def process_batch(
        self,
        files: List[Dict[str, Any]],
        preprocess_mode: str = "standard",
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> Dict[str, Any]:
        """Process a list of files where each file dict has {'name': str, 'content': bytes or Path}.

        Guarantees that an individual document failure does not cancel or corrupt other batch jobs.
        """
        batch_id = f"BATCH-{int(time.time())}-{uuid.uuid4().hex[:6].upper()}"
        total_files = len(files)
        results: List[Dict[str, Any]] = []

        success_count = 0
        failed_count = 0
        review_count = 0

        existing_invoices = self.repo.get_invoices(limit=500)

        for idx, file_info in enumerate(files, start=1):
            if isinstance(file_info, tuple) and len(file_info) >= 2:
                filename = str(file_info[0])
                content = file_info[1]
            elif isinstance(file_info, dict):
                filename = file_info.get("name") or file_info.get("filename") or f"document_{idx}"
                content = file_info.get("content")
            elif hasattr(file_info, "name") and (hasattr(file_info, "getvalue") or hasattr(file_info, "read")):
                filename = file_info.name
                content = file_info.getvalue() if hasattr(file_info, "getvalue") else file_info.read()
            else:
                filename = f"document_{idx}"
                content = file_info

            if progress_callback:
                progress_callback(idx, total_files, filename)

            try:
                # 1. OCR Processing
                ocr_res = self.engine.process_document(content, preprocess_mode=preprocess_mode)

                # 2. Field Extraction
                ext = FieldExtractor.extract_all(ocr_res["raw_text"])
                ext["raw_text"] = ocr_res["raw_text"]
                ext["filename"] = filename
                ext["batch_id"] = batch_id

                # 3. Duplicate Detection
                dup_check = DuplicateDetector.check_duplicate(ext, existing_invoices)
                if dup_check["is_duplicate"]:
                    ext["is_duplicate"] = 1
                    first_match = dup_check["matching_invoices"][0]
                    ext["duplicate_of_id"] = first_match.get("id")

                # 4. Accounting & Schema Validation
                schema, report = validate_invoice_payload(ext)

                # 5. Database Save
                inv_id = self.repo.save_invoice(
                    schema.model_dump(),
                    items=[i.model_dump() for i in schema.line_items],
                    filename=filename,
                )

                status = schema.validation_status
                if status == "VALIDATED":
                    success_count += 1
                else:
                    review_count += 1

                item_result = {
                    "filename": filename,
                    "invoice_id": inv_id,
                    "vendor_name": schema.vendor_name,
                    "invoice_number": schema.invoice_number,
                    "total_amount": schema.total_amount,
                    "currency": schema.currency,
                    "status": status,
                    "audit_grade": report["grade"],
                    "is_duplicate": dup_check["is_duplicate"],
                    "warnings": report.get("audit_flags", []) + dup_check.get("reasons", []),
                    "error": None,
                }
                results.append(item_result)

                # Update local list to detect duplicates within the same batch!
                existing_invoices.append(schema.model_dump())

            except Exception as e:
                failed_count += 1
                results.append({
                    "filename": filename,
                    "invoice_id": None,
                    "vendor_name": "Unprocessed",
                    "invoice_number": "N/A",
                    "total_amount": 0.0,
                    "currency": "USD",
                    "status": "FAILED",
                    "audit_grade": "FAILED",
                    "is_duplicate": False,
                    "warnings": [],
                    "error": str(e),
                })

        return {
            "batch_id": batch_id,
            "total_files": total_files,
            "success_count": success_count,
            "review_count": review_count,
            "failed_count": failed_count,
            "items": results,
            "results": results,
        }
