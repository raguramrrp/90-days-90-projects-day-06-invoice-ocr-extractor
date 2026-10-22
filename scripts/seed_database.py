"""Seed Database Script.

Processes and loads the 5 sample invoices into the SQLite database
so the application can be explored with data immediately out of the box.
"""

from __future__ import annotations

import glob
from pathlib import Path
import sys

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config
from src.database.repository import InvoiceRepository
from src.ocr.engine import OCREngine
from src.parser.extractor import FieldExtractor
from src.validator.schema_validator import validate_invoice_payload


def seed() -> None:
    """Process all sample invoices and populate the SQLite database."""
    print("Initializing Database Seeder...")
    repo = InvoiceRepository()
    engine = OCREngine()

    sample_dir = config.BASE_DIR / "data" / "sample_invoices"
    png_files = sorted(list(sample_dir.glob("*.png")))

    if not png_files:
        print("No sample PNG files found. Running generator first...")
        from scripts.generate_sample_invoices import generate_all_samples
        generate_all_samples()
        png_files = sorted(list(sample_dir.glob("*.png")))

    for f in png_files:
        filename = f.name
        print(f"  Processing {filename}...")
        res = engine.process_document(f)
        ext = FieldExtractor.extract_all(res["raw_text"])
        ext["raw_text"] = res["raw_text"]
        ext["filename"] = filename

        schema, report = validate_invoice_payload(ext)

        inv_id = repo.save_invoice(
            schema.model_dump(),
            items=[i.model_dump() for i in schema.line_items],
            filename=filename,
        )
        print(f"    -> Saved #{inv_id}: {schema.vendor_name} ({schema.invoice_number}) [Grade: {report['grade']}]")

    print("\nDatabase seeded successfully!")
    analytics = repo.get_analytics_summary()
    print(f"Total Invoices: {analytics['total_invoices']} | Total Spend: ${analytics['total_spend']:,.2f}")


if __name__ == "__main__":
    seed()
