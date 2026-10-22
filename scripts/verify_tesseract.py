"""Diagnostic script to verify Tesseract OCR installation and OpenCV preprocessing."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config
from src.ocr.engine import OCREngine


def main() -> None:
    print("=" * 60)
    print("  INVOICE OCR SYSTEM — DIAGNOSTIC & VERIFICATION TOOL")
    print("=" * 60)

    diag = config.get_system_diagnostics()
    print(f"Project Directory     : {diag['base_dir']}")
    print(f"Database Path         : {diag['database_path']}")
    print(f"Tesseract Path Found  : {diag['tesseract_executable']}")
    print(f"OCR Engine Available  : {diag['ocr_available']}")
    print(f"Tesseract Version     : {diag['ocr_version']}")

    engine = OCREngine()
    if engine.is_available():
        print("\n[SUCCESS] Tesseract OCR is correctly configured and operational.")
        print(f"Engine Version: {engine.get_version()}")
    else:
        print("\n[WARNING] Tesseract OCR binary not found.")
        print("To install Tesseract on Windows:")
        print("  1. Run in PowerShell: winget install UB-Mannheim.TesseractOCR")
        print("  2. Or download installer from: https://github.com/UB-Mannheim/tesseract/wiki")
        print("  3. Set TESSERACT_CMD in .env if installed to a custom directory.")

    print("=" * 60)


if __name__ == "__main__":
    main()
