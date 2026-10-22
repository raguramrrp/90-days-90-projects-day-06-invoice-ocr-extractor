# Project Overview: Automated Invoice Data Extraction & Structuring System

## 1. Executive Summary
The **Automated Invoice Data Extraction & Structuring System** is a Computer Vision, Document AI, and FinTech automation application designed to eliminate manual data entry of invoice information. By ingesting invoice images (PNG, JPG, TIFF) or digital PDFs, the system applies image enhancement filters, extracts character streams using Tesseract OCR, structures business entities via rule-based NLP and regular expressions, reconciles accounting totals, and persists validated records into an SQLite database with JSON/CSV export capabilities.

---

## 2. Problem Statement
In finance, procurement, and accounting departments, accounts payable specialists spend thousands of manual hours transcribing paper, scanned, and digital invoices into ERP and accounting databases. This manual transcription workflow suffers from:
- **High Operational Costs**: Manual keying costs between $12 to $30 per invoice according to industry benchmarks.
- **Data Entry Errors**: Transposition mistakes, missed decimals, and misread vendor names lead to billing disputes and duplicate payments.
- **Latency**: Processing cycles often take 5 to 15 days, delaying vendor payments and causing missed early-payment discounts.

---

## 3. The Solution
This project implements an end-to-end, automated document intelligence pipeline:
1. **Document Ingestion**: Accepts multi-format image files (PNG, JPG, TIFF) or digital PDFs.
2. **Computer Vision Preprocessing**: Normalizes document scans via grayscale conversion, bilateral edge-preserving smoothing, minimum bounding box deskewing, and Otsu binarization.
3. **Optical Character Recognition**: Interfaces with Tesseract OCR (PSM 4) to extract text and spatial coordinates with confidence ratings.
4. **Information Extraction Engine**: Parses vendor names, invoice numbers, dates, payment terms, PO numbers, and line items using regular expressions, reverse token matching, and heuristic entity filtering.
5. **Accounting Balance Verification**: Mathematically verifies that:
   $$\text{Subtotal} + \text{Tax} + \text{Shipping} - \text{Discount} = \text{Total Amount}$$
6. **Persistence & Export**: Stores records in SQLite with relational line items and provides formatted JSON and CSV exports.

---

## 4. Domain & Target Audience
- **Domain**: Computer Vision / Document Processing / FinTech Automation
- **Target Audience**:
  - Accounts Payable (AP) and procurement teams
  - Small and medium-sized businesses handling high invoice volumes
  - Developers and recruiters evaluating AI/Data Science engineering capabilities

---

## 5. Scope & MVP Boundaries
### In-Scope (Day 6 MVP Deliverables)
- Image and PDF document ingestion.
- OpenCV preprocessing pipeline (deskewing, denoising, adaptive binarization, DPI scaling).
- Tesseract OCR integration with word-level bounding boxes and confidence scores.
- Entity extraction for Vendor Name, Invoice Number, Issue Date, Due Date, Currency, Subtotal, Tax, Shipping, Discount, Total Due, PO Number, and Payment Terms.
- Itemized line item table parsing.
- Accounting reconciliation validation engine.
- SQLite database storage with foreign-key relational integrity (`invoices`, `invoice_items`).
- Modern Streamlit multi-tab user interface.
- 5 bundled, realistic synthetic sample invoices in both PDF and PNG formats.
- Complete automated test suite (`pytest`) with 27 unit and integration tests.
- Single-click Windows setup scripts (`setup.bat`, `run.bat`, `test.bat`).

### Out-of-Scope (Future Upgrades)
- Real-time foreign exchange currency conversion APIs.
- Direct OAuth2 connector to external ERPs (SAP, QuickBooks, Xero).
- Multilingual OCR for non-Latin script alphabets (e.g., Arabic, Cyrillic, Kanji).
- Fraud detection via digital forensic signature verification.
