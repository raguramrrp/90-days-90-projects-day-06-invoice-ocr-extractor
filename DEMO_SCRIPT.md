# 60–120 Second Portfolio Demonstration Script
### *INVOICE INTELLIGENCE: Document Processing & Financial Operations Platform*

**Target Audience**: Technical Recruiters, Engineering Managers, FinTech & Document AI Interviewers  
**Setup**: Run `run.bat` and open `http://localhost:8501`.

---

## Act 1: The Problem & The Transformation (0:00 – 0:25)
> *"Hello! Most accounts payable teams still manually key invoice numbers, dates, line items, and totals into their accounting software. This causes data entry errors, costly duplicate disbursements, and weeks of reconciliation delay.
>
> For Day 6 of my 90 Days Challenge, I transformed a basic OCR utility into **INVOICE INTELLIGENCE** — a financial document processing and operations platform built around the complete accounts payable lifecycle:
>
> Capture, Extract, Validate, Reconcile, Review, Approve, Export, and Audit."*

---

## Act 2: Operations Desk & Information Architecture (0:25 – 0:50)
> *(Action: Show the Overview screen and toggle between Editorial Light and Dark theme)*
>
> *"Notice the information architecture: instead of a generic AI template, it’s organized into four core operational areas: Workspace, Document Operations, Financial Operations, and System.
>
> On the Overview Operations Desk, metrics are strictly partitioned by currency denomination — no misleading combinations of USD and EUR. We track our live invoice pipeline stages from Imported through Reconciled to Exported, and highlight immediate work requiring attention.
>
> Next, let's look at **My Work Queue**: tasks are automatically grouped by actionable issue — missing vendor names, inverted date chronologies, math imbalances, or duplicate alerts, sorted by priority for rapid resolution."*

---

## Act 3: Extraction Studio & Dual-Pane Workstation (0:50 – 1:20)
> *(Action: Open Extraction Studio with a multi-item sample invoice)*
>
> *"In the Extraction Studio, we have a document-first split-screen review workstation:
> - On the left, our OpenCV pipeline deskews tilt, filters background noise, and passes text to Tesseract OCR in Page Segmentation Mode 4. Operators have a zoom slider, page navigation, and confidence-colored bounding boxes.
> - On the right, our reverse-token table parser extracts line items and prices. Crucially, our live Accounting Balance Visualizer enforces domain integrity: verifying that Subtotal plus Tax plus Shipping minus Discount equals the Total Due, flagging discrepancies down to the penny.
> - Operators can edit fields, modify line items inline with an interactive data grid, and commit records with an immutable audit trail entry tracking field changes."*

---

## Act 4: Duplicate Review, Vendors & Multi-Sheet Excel Export (1:20 – 1:50)
> *(Action: Click 'Duplicate Review', then 'Vendors', then 'Reports & Exports')*
>
> *"Double-billing is an enormous corporate risk. In our **Duplicate Review** workspace, our multi-signal engine pairs candidate duplicates side-by-side — comparing normalized vendors, invoice numbers, dates, and amounts, allowing operators to mark candidates as Confirmed Duplicates or Legitimate Separate billings.
>
> In **Vendors**, spend is aggregated by currency with transaction timelines and a safe Vendor Rename tool that normalizes vendor names across all historical records with full audit diffs.
>
> In **Reports & Exports**, users can download structured JSON, CSVs, or a multi-sheet Excel workbook generated with openpyxl — containing the Invoices Register, Itemized Line Items, Audit Summary, Validation Exceptions, and Duplicate Review Candidates, with built-in Formula Injection Defense against spreadsheet macro exploits."*

---

## Closing Summary (1:50 – 2:00)
> *"The platform runs 100% locally on Windows, is backed by 44 automated unit and integration tests passing in under 6 seconds, and represents production-grade Document AI and FinTech software engineering."*
