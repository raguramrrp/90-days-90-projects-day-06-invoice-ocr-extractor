# User Guide: INVOICE INTELLIGENCE
### *Document Processing & Financial Operations Platform*

Welcome to **Invoice Intelligence**, an enterprise document processing and financial operations platform designed for finance teams, accounts payable (AP) specialists, and business operations.

---

## 1. Quick Launch
Start the platform using the automated Windows launcher:
```cmd
run.bat
```
Or directly via the virtual environment:
```cmd
.venv\Scripts\streamlit.exe run app.py
```
Access the application at **`http://localhost:8501`**.

---

## 2. Information Architecture & Navigation

The navigation is divided into 4 core functional sections across 13 dedicated workspaces:

```text
├── WORKSPACE
│   ├── Overview                  # Actionable Operations Desk & Pipeline Progress
│   ├── My Work Queue             # Task-oriented exception inbox
│   ├── All Invoices              # Full relational ledger & search
│   └── Vendors                   # Counterparty directory & normalization
├── DOCUMENT OPERATIONS
│   ├── Import Center             # Multi-document ingestion & batch queue
│   ├── Extraction Studio         # Split-screen document review workstation
│   ├── Validation & Exceptions   # Rules-based audit engine
│   └── Duplicate Review          # Side-by-side candidate pair comparison
├── FINANCIAL OPERATIONS
│   ├── Reconciliation            # Invoice-level financial consistency check
│   ├── Financial Insights        # Currency-segregated analytics & spend trends
│   └── Reports & Exports         # Excel (.xlsx), CSV, and JSON export center
└── SYSTEM
    ├── Activity & Audit          # Full governance trail & batch logs
    └── Settings                  # System diagnostics & sample database re-seeding
```

---

## 3. Workspaces Walkthrough

### 3.1 Overview (Actionable Operations Desk)
- **Operational Summary Cards**: Total Invoices in ledger, Volume segregated by currency denomination, Active Work Queue count, Active Exceptions, and Flagged Duplicate Candidates.
- **Invoice Pipeline Tracker**: Live stage progression tracker:
  $$\text{Imported} \longrightarrow \text{Extracted} \longrightarrow \text{Under Review} \longrightarrow \text{Validated} \longrightarrow \text{Reconciled} \longrightarrow \text{Exported}$$
- **Work Requiring Attention**: High-priority alert list of missing fields, math imbalances, and duplicate warnings with direct **"Resolve"** shortcuts.
- **Recent Processing Activity**: Chronological audit feed tracking recent extractions, edits, and reconciliations.

### 3.2 My Work Queue
- **Task-Oriented Exception Inbox**: Invoices requiring human attention are automatically routed here.
- **Categories**:
  - `MISSING_INFO`: Missing critical fields (vendor, invoice number, date, total).
  - `VALIDATION_FAILED`: Imbalances, invalid dates, or schema audit flags.
  - `POTENTIAL_DUPLICATE`: Flagged duplicate candidate awaiting decision.
  - `RECONCILIATION_REQUIRED`: Mathematical mismatch between stated and calculated totals.
  - `NEEDS_REVIEW`: General extractions awaiting final operator sign-off.
- **Priority Sorting**: High, Medium, and Low severity tasks.
- **Resolution**: Click "Open in Studio" or "Reconcile" to immediately fix and resolve the issue. Resolving removes the task from the active queue.

### 3.3 All Invoices (Primary Ledger)
- **Multi-Criteria Search**: Search across vendor name, invoice number, or PO number.
- **Filters**: Validation status (`VALIDATED`, `VERIFIED_WITH_WARNINGS`, `NEEDS_REVIEW`), currency (`USD`, `EUR`, `GBP`, etc.), and sorting.
- **Record Inspector**: Select any invoice ID to open its full metadata breakdown, itemized line items table, and immutable audit trail entries.
- **Management**: Reconcile, edit in studio, or permanently delete records.

### 3.4 Vendors (Directory & Counterparty Governance)
- **Aggregated Directory**: Real-time roll-up of all counterparties.
- **Currency Segregation**: Spend totals partitioned strictly by currency (no misleading USD + EUR sums).
- **Date Tracking**: First transaction date and latest invoice date.
- **Vendor Rename & Normalization**: Correct misspelled or duplicate vendor variations (e.g. `Apex Hardware Inc.` to `Apex Hardware Labs LLC`) across all associated historical invoices with automated audit trail logging.

### 3.5 Import Center
- **Multi-Document Ingestion**: Drag and drop multiple invoices (`.png`, `.jpg`, `.jpeg`, `.tiff`, `.pdf`).
- **Independent Failure Isolation**: If an individual document is corrupt or unreadable, the failure is isolated to that file while the rest of the batch completes successfully.
- **Queue Preview**: Displays filenames, file sizes, and status before processing.
- **Demo Samples Loader**: Instant one-click ingestion of curated synthetic sample invoices.

### 3.6 Extraction Studio (Split-Screen Review Workstation)
- **Dual-Pane Layout**:
  - **Left Pane (Document Viewer)**:
    - Multi-page PDF navigation (*Previous / Next*).
    - High-resolution **Zoom Slider** ($50\%$ to $250\%$) for fine-print receipt verification.
    - Inspection layers: *Original Document*, *Preprocessed Binary*, *OCR Bounding Boxes* (color-coded by confidence: Green $\ge 80\%$, Amber $50\text{--}79\%$, Red $< 50\%$), and *Recognized Plain Text*.
  - **Right Pane (Structured Data Editor)**:
    - **Live Accounting Formula Visualizer**:
      $$\text{Subtotal} + \text{Tax} + \text{Shipping} - \text{Discount} = \text{Total Due}$$
      Live discrepancy calculation with color-coded audit status (`EXCELLENT`, `GOOD`, `NEEDS_REVIEW`).
    - **Metadata Form**: Real-time editable fields for Vendor Name, Invoice #, PO #, Invoice Date, Due Date, Currency, and Payment Terms.
    - **Interactive Line-Items Data Grid**: Fully editable tabular grid to add, edit, or delete items, quantities, unit prices, and line amounts with row math checks.
    - **Duplicate Alert**: Automatic cross-referencing against database records with match reasons.
    - **Commit to Ledger**: Saves verified invoices directly to SQLite with audit diff logging.

### 3.7 Validation & Exceptions
- **Rules-Based Audit Engine**: Evaluates invoices against financial business rules:
  - Missing vendor, invoice number, date, or zero totals.
  - Date chronology (due date preceding issue date).
  - Mathematical balance imbalances ($|\Delta| > \$0.05$).
  - Line-items sum vs subtotal mismatches.
  - Line-item row arithmetic ($\text{Qty} \times \text{Unit Price} \ne \text{Amount}$).
- **Severity Breakdown**: Filter by `CRITICAL`, `WARNING`, or `INFO`.
- **Direct Fix**: Click "Fix in Studio" to resolve the issue on the specific invoice.

### 3.8 Duplicate Review
- **Candidate Pair Comparison**: Inspects potential duplicate billings detected by `DuplicateDetector`:
  - **Exact Duplicates**: Identical normalized vendor and invoice number.
  - **Suspected Duplicates**: Identical vendor, date, and amount with slight variations in invoice numbers.
- **Side-by-Side Review**: Compare Record A vs Record B attributes.
- **Decisions**: Click **"Confirm Duplicate"** or **"Mark Legitimate Separate"** with operator audit notes.

### 3.9 Reconciliation
- **Invoice-Level Financial Consistency**: Verifies arithmetic equations and flags discrepancy amounts.
- **Review Actions**: One-click **"Mark Reconciled"** or **"Adjust in Studio"**.

### 3.10 Financial Insights
- **Currency-Segregated Spend**: Dedicated KPI cards for each currency denomination.
- **Top Vendors Concentration**: Horizontal bar chart of spending by counterparty.
- **Monthly Spend Trend**: Line chart tracking monthly expenditure over time.

### 3.11 Reports & Exports
- **Multi-Sheet Excel Workbook (`.xlsx`)**:
  - Sheet 1: `Invoices Register`
  - Sheet 2: `Itemized Line Items`
  - Sheet 3: `Audit Summary`
  - Sheet 4: `Validation Exceptions`
  - Sheet 5: `Duplicate Review Candidates`
  - **Formula Injection Sanitization**: Prepends single quotes (`'`) to values starting with `=`, `+`, `-`, `@`, `\t`, or `\r`.
- **Structured JSON**: ERP-compatible payload with nested line items.
- **Summary & Line-Items CSVs**: Standard comma-separated tabular files.

### 3.12 Activity & Audit
- System-wide immutable audit trail table tracking all field modifications, previous values, new values, operator identities, and timestamps.
- Filter by action type: `ALL`, `CREATION`, `STUDIO_EDIT`, `USER_EDIT`, `RECONCILIATION`, `DUPLICATE_REVIEW`, `VENDOR_RENAME`.

### 3.13 Settings
- Live OCR engine diagnostics (Tesseract binary path, version detection, language packs).
- SQLite database file size and PRAGMA integrity check.
- **Re-seed Sample Invoices**: Restores clean synthetic test invoices for presentations or testing.
