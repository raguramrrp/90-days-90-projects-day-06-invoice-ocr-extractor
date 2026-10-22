# Testing & Quality Assurance Report
### *INVOICE INTELLIGENCE Platform*

## 1. Test Suite Summary
The project includes a comprehensive, automated test suite built with `pytest`. All 44 tests execute cleanly in under 6 seconds on Windows.

```text
============================= test session starts =============================
platform win32 -- Python 3.12.6, pytest-9.1.1, pluggy-1.7.0
rootdir: D:\90 days\90-days-90-projects-day-06-invoice-ocr-extractor
configfile: pyproject.toml
collected 44 items

tests/test_batch_manager.py::test_batch_processing_multiple_samples PASSED [  2%]
tests/test_batch_manager.py::test_batch_error_isolation PASSED           [  4%]
tests/test_database.py::test_save_and_retrieve_invoice PASSED            [  6%]
tests/test_database.py::test_update_invoice PASSED                       [  9%]
tests/test_database.py::test_delete_invoice PASSED                       [ 11%]
tests/test_database.py::test_analytics_summary PASSED                    [ 13%]
tests/test_duplicate_detector.py::test_normalize_vendor PASSED           [ 15%]
tests/test_duplicate_detector.py::test_normalize_invoice_number PASSED   [ 18%]
tests/test_duplicate_detector.py::test_exact_duplicate_detection PASSED  [ 20%]
tests/test_duplicate_detector.py::test_suspected_duplicate_detection PASSED [ 22%]
tests/test_duplicate_detector.py::test_no_duplicate PASSED               [ 25%]
tests/test_e2e_pipeline.py::test_e2e_sample_invoice_processing PASSED    [ 27%]
tests/test_engine.py::test_engine_availability PASSED                    [ 29%]
tests/test_engine.py::test_ocr_text_extraction PASSED                    [ 31%]
tests/test_engine.py::test_word_boxes_and_confidence PASSED              [ 34%]
tests/test_engine.py::test_draw_visual_boxes PASSED                      [ 36%]
tests/test_excel_exporter.py::test_sanitize_formula_injection PASSED     [ 38%]
tests/test_excel_exporter.py::test_export_to_excel PASSED                [ 40%]
tests/test_exporter.py::test_export_to_json PASSED                       [ 43%]
tests/test_exporter.py::test_export_summary_csv PASSED                   [ 45%]
tests/test_exporter.py::test_export_detailed_items_csv PASSED            [ 47%]
tests/test_extractor.py::test_clean_amount PASSED                        [ 50%]
tests/test_extractor.py::test_parse_date_to_iso PASSED                   [ 52%]
tests/test_extractor.py::test_extract_vendor_heuristic PASSED            [ 54%]
tests/test_extractor.py::test_field_extractor_full_document PASSED       [ 56%]
tests/test_math_validator.py::test_math_validator_exact_match PASSED     [ 59%]
tests/test_math_validator.py::test_math_validator_discrepancy PASSED     [ 61%]
tests/test_schema_validator.py::test_schema_validator_audit_grade PASSED   [ 63%]
tests/test_preprocessor.py::test_load_as_cv2_from_pil PASSED             [ 65%]
tests/test_preprocessor.py::test_to_grayscale PASSED                     [ 68%]
tests/test_preprocessor.py::test_rescale PASSED                          [ 70%]
tests/test_preprocessor.py::test_binarize_otsu PASSED                    [ 72%]
tests/test_preprocessor.py::test_pipeline_modes PASSED                   [ 75%]
tests/test_rule_engine.py::test_rule_missing_vendor_and_invoice_no PASSED [ 77%]
tests/test_rule_engine.py::test_rule_date_chronology PASSED              [ 79%]
tests/test_rule_engine.py::test_rule_math_imbalance PASSED               [ 81%]
tests/test_rule_engine.py::test_rule_line_item_arithmetic PASSED         [ 84%]
tests/test_table_parser.py::test_parse_multi_column_items PASSED         [ 86%]
tests/test_table_parser.py::test_parse_single_amount_service PASSED      [ 88%]
tests/test_table_parser.py::test_ignore_terminator_lines PASSED          [ 90%]
tests/test_work_queue.py::test_work_queue_categorization PASSED          [ 93%]
tests/test_work_queue.py::test_vendor_directory_and_rename PASSED        [ 95%]
tests/test_work_queue.py::test_find_duplicate_pairs_and_record_decision PASSED [ 97%]
tests/test_work_queue.py::test_export_exceptions_and_duplicates_csv PASSED [100%]

============================= 44 passed in 5.63s ==============================
```

---

## 2. Test Cases Breakdown by Module

### 2.1 Rules-Based Exception Engine (`tests/test_rule_engine.py`)
| Test Case | Description | Result |
| :--- | :--- | :---: |
| `test_rule_missing_vendor_and_invoice_no` | Verifies detection of critical missing vendor and invoice number | **PASS** |
| `test_rule_date_chronology` | Flags warning when due date precedes invoice issuance date | **PASS** |
| `test_rule_math_imbalance` | Flags critical exception when $\text{Subtotal} + \text{Tax} + \text{Shipping} - \text{Discount} \ne \text{Total}$ | **PASS** |
| `test_rule_line_item_arithmetic` | Flags info finding when $\text{Qty} \times \text{Unit Price} \ne \text{Line Total}$ | **PASS** |

### 2.2 Work Queue, Vendor Directory & Reconcile (`tests/test_work_queue.py`)
| Test Case | Description | Result |
| :--- | :--- | :---: |
| `test_work_queue_categorization` | Tests routing invoices into `MISSING_INFO`, `VALIDATION_FAILED`, etc. | **PASS** |
| `test_vendor_directory_and_rename` | Tests vendor grouping, spend aggregation, and safe rename with audit logging | **PASS** |
| `test_find_duplicate_pairs_and_record_decision` | Tests pair discovery and saving duplicate review decision | **PASS** |
| `test_export_exceptions_and_duplicates_csv` | Tests serialization of validation exceptions and duplicate pairs to CSV | **PASS** |

### 2.3 Batch Processing Engine (`tests/test_batch_manager.py`)
| Test Case | Description | Result |
| :--- | :--- | :---: |
| `test_batch_processing_multiple_samples` | Tests multi-file ingestion across sample invoices | **PASS** |
| `test_batch_error_isolation` | Verifies independent failure isolation when a corrupt document is injected | **PASS** |

### 2.4 Duplicate Invoice Detection (`tests/test_duplicate_detector.py`)
| Test Case | Description | Result |
| :--- | :--- | :---: |
| `test_normalize_vendor` | Verifies vendor normalization (lowercasing, legal suffix removal) | **PASS** |
| `test_normalize_invoice_number` | Strips punctuation, whitespace, and leading symbols | **PASS** |
| `test_exact_duplicate_detection` | Flags exact duplicates matching normalized vendor and number | **PASS** |
| `test_suspected_duplicate_detection` | Detects suspected duplicates sharing vendor, date, and amount | **PASS** |
| `test_no_duplicate` | Confirms unique invoices pass without false positives | **PASS** |

### 2.5 Excel Export & Security (`tests/test_excel_exporter.py`)
| Test Case | Description | Result |
| :--- | :--- | :---: |
| `test_sanitize_formula_injection` | Verifies single-quote escaping of formula triggers (`=`, `+`, `-`, `@`, `\t`, `\r`) | **PASS** |
| `test_export_to_excel` | Verifies multi-sheet workbook generation via `openpyxl` | **PASS** |

### 2.6 Computer Vision Preprocessing (`tests/test_preprocessor.py`)
| Test Case | Description | Result |
| :--- | :--- | :---: |
| `test_load_as_cv2_from_pil` | Converts PIL images to standard OpenCV BGR arrays | **PASS** |
| `test_to_grayscale` | Ensures 3-channel BGR images convert to 1-channel luminance | **PASS** |
| `test_rescale` | Tests bicubic interpolation scaling by factor of 2.0x | **PASS** |
| `test_binarize_otsu` | Confirms pixel values are strictly binary $\{0, 255\}$ | **PASS** |
| `test_pipeline_modes` | Validates pipeline modes (`standard`, `grayscale_only`, `none`) | **PASS** |

### 2.7 OCR Engine & Spatial Bounding Boxes (`tests/test_engine.py`)
| Test Case | Description | Result |
| :--- | :--- | :---: |
| `test_engine_availability` | Verifies local Tesseract discovery and version check | **PASS** |
| `test_ocr_text_extraction` | Tests OCR extraction on synthetic test images | **PASS** |
| `test_word_boxes_and_confidence` | Checks coordinate boxes `(x, y, w, h)` and confidence intervals | **PASS** |
| `test_draw_visual_boxes` | Validates color-coded bounding box rendering overlays | **PASS** |

### 2.8 Field Extraction & NLP Rules (`tests/test_extractor.py`)
| Test Case | Description | Result |
| :--- | :--- | :---: |
| `test_clean_amount` | Tests currency detection and numeric conversion ($1,250.50, €450, ₹15,000) | **PASS** |
| `test_parse_date_to_iso` | Normalizes European, American, and verbal dates to ISO `YYYY-MM-DD` | **PASS** |
| `test_extract_vendor_heuristic` | Verifies business entity recognition and stopword exclusion | **PASS** |
| `test_field_extractor_full_document` | Tests complete extraction on simulated invoice text | **PASS** |

### 2.9 Table Parser (`tests/test_table_parser.py`)
| Test Case | Description | Result |
| :--- | :--- | :---: |
| `test_parse_multi_column_items` | Extracts description, qty, unit price, and total amount | **PASS** |
| `test_parse_single_amount_service` | Handles service invoices with single line amounts | **PASS** |
| `test_ignore_terminator_lines` | Terminates table parsing upon encountering summary keywords | **PASS** |

### 2.10 Accounting Balance Validator (`tests/test_math_validator.py`)
| Test Case | Description | Result |
| :--- | :--- | :---: |
| `test_math_validator_exact_match` | Verifies $300 + 30 + 10 - 20 = 320$ passes with 0 discrepancy | **PASS** |
| `test_math_validator_discrepancy` | Flags discrepancy when extracted total differs from calculated sum | **PASS** |
| `test_schema_validator_audit_grade` | Tests Pydantic validation and assignment of `EXCELLENT` grade | **PASS** |

### 2.11 Relational Database Repository (`tests/test_database.py`)
| Test Case | Description | Result |
| :--- | :--- | :---: |
| `test_save_and_retrieve_invoice` | Persists invoice and line items with foreign key | **PASS** |
| `test_update_invoice` | Updates fields and atomically replaces child line items | **PASS** |
| `test_delete_invoice` | Tests cascading delete of invoice and child items | **PASS** |
| `test_analytics_summary` | Verifies executive KPI aggregations (spend, average, top vendors) | **PASS** |

### 2.12 Exporters (`tests/test_exporter.py`)
| Test Case | Description | Result |
| :--- | :--- | :---: |
| `test_export_to_json` | Validates indented JSON serialization of invoices and nested items | **PASS** |
| `test_export_summary_csv` | Tests generation of CSV summary records | **PASS** |
| `test_export_detailed_items_csv` | Tests generation of normalized, flattened item-level CSV | **PASS** |

### 2.13 End-to-End Pipeline Integration (`tests/test_e2e_pipeline.py`)
| Test Case | Description | Result |
| :--- | :--- | :---: |
| `test_e2e_sample_invoice_processing` | Full lifecycle test from physical invoice image to OCR, extraction, validation, SQLite commit, and JSON/CSV export | **PASS** |

---

## 3. How to Execute Tests
```cmd
test.bat
```
Or directly using pytest:
```cmd
.venv\Scripts\pytest.exe -v
```
To run tests with code coverage:
```cmd
.venv\Scripts\pytest.exe --cov=src --cov-report=term-missing
```
