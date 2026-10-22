# Testing & Quality Assurance Report

## 1. Test Suite Summary
The project includes a comprehensive, automated test suite built with `pytest`. All 27 tests execute cleanly in under 3 seconds.

```text
============================= test session starts =============================
platform win32 -- Python 3.12.6, pytest-9.1.1, pluggy-1.7.0
rootdir: D:\90 days\90-days-90-projects-day-06-invoice-ocr-extractor
configfile: pyproject.toml
collected 27 items

tests/test_database.py::test_save_and_retrieve_invoice PASSED            [  3%]
tests/test_database.py::test_update_invoice PASSED                       [  7%]
tests/test_database.py::test_delete_invoice PASSED                       [ 11%]
tests/test_database.py::test_analytics_summary PASSED                    [ 14%]
tests/test_e2e_pipeline.py::test_e2e_sample_invoice_processing PASSED    [ 18%]
tests/test_engine.py::test_engine_availability PASSED                    [ 22%]
tests/test_engine.py::test_ocr_text_extraction PASSED                    [ 25%]
tests/test_engine.py::test_word_boxes_and_confidence PASSED              [ 29%]
tests/test_engine.py::test_draw_visual_boxes PASSED                      [ 33%]
tests/test_exporter.py::test_export_to_json PASSED                       [ 37%]
tests/test_exporter.py::test_export_summary_csv PASSED                   [ 40%]
tests/test_exporter.py::test_export_detailed_items_csv PASSED            [ 44%]
tests/test_extractor.py::test_clean_amount PASSED                        [ 48%]
tests/test_extractor.py::test_parse_date_to_iso PASSED                   [ 51%]
tests/test_extractor.py::test_extract_vendor_heuristic PASSED            [ 55%]
tests/test_extractor.py::test_field_extractor_full_document PASSED       [ 59%]
tests/test_math_validator.py::test_math_validator_exact_match PASSED     [ 62%]
tests/test_math_validator.py::test_math_validator_discrepancy PASSED     [ 66%]
tests/test_math_validator.py::test_schema_validator_audit_grade PASSED   [ 70%]
tests/test_preprocessor.py::test_load_as_cv2_from_pil PASSED             [ 74%]
tests/test_preprocessor.py::test_to_grayscale PASSED                     [ 77%]
tests/test_preprocessor.py::test_rescale PASSED                          [ 81%]
tests/test_preprocessor.py::test_binarize_otsu PASSED                    [ 85%]
tests/test_preprocessor.py::test_pipeline_modes PASSED                   [ 88%]
tests/test_table_parser.py::test_parse_multi_column_items PASSED         [ 92%]
tests/test_table_parser.py::test_parse_single_amount_service PASSED      [ 96%]
tests/test_table_parser.py::test_ignore_terminator_lines PASSED          [100%]

============================= 27 passed in 2.87s ==============================
```

---

## 2. Test Cases Breakdown by Module

### 2.1 Computer Vision Preprocessing (`tests/test_preprocessor.py`)
| Test Case | Description | Result |
| :--- | :--- | :---: |
| `test_load_as_cv2_from_pil` | Verifies conversion from PIL Image to standard OpenCV BGR NumPy array | **PASS** |
| `test_to_grayscale` | Ensures 3-channel BGR images convert to 1-channel luminance arrays | **PASS** |
| `test_rescale` | Tests bicubic interpolation scaling by factor of 2.0x | **PASS** |
| `test_binarize_otsu` | Confirms pixel values are strictly binary $\{0, 255\}$ | **PASS** |
| `test_pipeline_modes` | Validates pipeline modes (`standard`, `grayscale_only`, `none`) | **PASS** |

### 2.2 OCR Engine & Spatial Bounding Boxes (`tests/test_engine.py`)
| Test Case | Description | Result |
| :--- | :--- | :---: |
| `test_engine_availability` | Verifies Tesseract binary discovery and returns valid version | **PASS** |
| `test_ocr_text_extraction` | Tests optical character recognition on synthetic test images | **PASS** |
| `test_word_boxes_and_confidence` | Checks extraction of coordinate boxes `(x, y, w, h)` and confidence | **PASS** |
| `test_draw_visual_boxes` | Validates color-coded bounding box rendering on image overlays | **PASS** |

### 2.3 Field Extraction & NLP Rules (`tests/test_extractor.py`)
| Test Case | Description | Result |
| :--- | :--- | :---: |
| `test_clean_amount` | Tests currency detection and numeric conversion ($1,250.50, €450, ₹15,000) | **PASS** |
| `test_parse_date_to_iso` | Normalizes European, American, and verbal dates to ISO `YYYY-MM-DD` | **PASS** |
| `test_extract_vendor_heuristic` | Verifies business entity recognition and stopword exclusion | **PASS** |
| `test_field_extractor_full_document` | Tests complete extraction on simulated invoice text | **PASS** |

### 2.4 Table Parser (`tests/test_table_parser.py`)
| Test Case | Description | Result |
| :--- | :--- | :---: |
| `test_parse_multi_column_items` | Extracts description, qty, unit price, and total amount | **PASS** |
| `test_parse_single_amount_service` | Handles service invoices with single line amounts | **PASS** |
| `test_ignore_terminator_lines` | Terminates table parsing upon encountering summary keywords | **PASS** |

### 2.5 Accounting Balance Validator (`tests/test_math_validator.py`)
| Test Case | Description | Result |
| :--- | :--- | :---: |
| `test_math_validator_exact_match` | Verifies $300 + 30 + 10 - 20 = 320$ passes with 0 discrepancy | **PASS** |
| `test_math_validator_discrepancy` | Flags discrepancy when extracted total differs from calculated sum | **PASS** |
| `test_schema_validator_audit_grade` | Tests Pydantic validation and assignment of `EXCELLENT` grade | **PASS** |

### 2.6 Relational Database Repository (`tests/test_database.py`)
| Test Case | Description | Result |
| :--- | :--- | :---: |
| `test_save_and_retrieve_invoice` | Persists parent invoice and child line items with foreign key | **PASS** |
| `test_update_invoice` | Updates fields and atomically replaces child line items | **PASS** |
| `test_delete_invoice` | Tests cascading delete of invoice and child items | **PASS** |
| `test_analytics_summary` | Verifies executive KPI aggregations (spend, average, top vendors) | **PASS** |

### 2.7 Exporters (`tests/test_exporter.py`)
| Test Case | Description | Result |
| :--- | :--- | :---: |
| `test_export_to_json` | Validates indented JSON serialization of invoices and nested items | **PASS** |
| `test_export_summary_csv` | Tests generation of CSV summary records | **PASS** |
| `test_export_detailed_items_csv` | Tests generation of normalized, flattened item-level CSV | **PASS** |

### 2.8 End-to-End Pipeline Integration (`tests/test_e2e_pipeline.py`)
| Test Case | Description | Result |
| :--- | :--- | :---: |
| `test_e2e_sample_invoice_processing` | Full lifecycle test from physical invoice image to OCR, extraction, validation, SQLite commit, and JSON/CSV export | **PASS** |

---

## 3. How to Execute Tests
To run all tests from Windows Command Prompt or PowerShell:
```cmd
test.bat
```
Or directly using the virtual environment pytest executable:
```cmd
.venv\Scripts\pytest.exe -v
```
To run tests with code coverage:
```cmd
.venv\Scripts\pytest.exe --cov=src --cov-report=term-missing
```
