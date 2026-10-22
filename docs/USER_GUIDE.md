# User Guide: Invoice OCR Extractor

This user guide walks you through the features and operating procedures of the Automated Invoice Data Extraction & Structuring System.

---

## 1. Quick Launch
Start the application using the automated Windows launcher:
```cmd
run.bat
```
Alternatively, invoke Streamlit directly:
```cmd
.venv\Scripts\streamlit.exe run app.py
```
Open your web browser at **`http://localhost:8501`**.

---

## 2. Navigating the Interface

### Sidebar Controls
- **System Health Indicator**: Displays whether Tesseract OCR is active and reports its detected version.
- **Quick Demo Invoices**: Dropdown containing 5 bundled sample invoices. Select any sample (e.g., `INV-2026-001_Apex_Hardware.png`) and click **"⚡ Load & Process This Sample"** to test immediately.
- **Preprocessing Tuning**:
  - *Thresholding Mode*: Choose between `standard` (Otsu binarization for crisp scans) or `adaptive` (Gaussian thresholding for smartphone photos with uneven lighting).
  - *Auto-Deskew*: Toggle automated rotation correction.
  - *Upscale Factor*: Adjust magnification ($1.0\times$ to $2.5\times$) for small receipt numbers.

---

### Tab 1: Upload & Extract
1. **Drop File**: Drag and drop an invoice image (`.png`, `.jpg`, `.jpeg`, `.tiff`) or digital PDF (`.pdf`) into the upload zone.
2. **Execute OCR**: Click **"🚀 Run OCR & Field Extraction"**.
3. **Inspect Output in Visual Inspector**:
   - *Original Document*: Displays raw document preview.
   - *Preprocessed Binary*: Displays the deskewed, thresholded black-and-white image fed into OCR.
   - *OCR Bounding Boxes*: Visualizes color-coded bounding boxes around detected words (Green $\ge 80\%$, Orange $50\text{--}79\%$, Red $< 50\%$).
   - *Raw Text*: Shows the full plain text recognized by Tesseract.

---

### Tab 2: Extracted Data & Review
1. **Validation Status Banner**:
   - `VALIDATED (EXCELLENT)`: All fields identified and math verified with \$0.00 discrepancy.
   - `VERIFIED WITH WARNINGS (GOOD)`: Financial balance verified, but minor non-critical fields require review.
   - `DISCREPANCY (NEEDS_REVIEW)`: Extracted numbers do not balance mathematically.
2. **Entity Cards**: Shows Vendor Name, Invoice Number, Issue Date, Due Date, Terms, and PO Number with individual confidence percentages.
3. **Accounting Reconciliation Equation**: Shows:
   $$\text{Subtotal} + \text{Tax} + \text{Shipping} - \text{Discount} = \text{Total Due}$$
4. **Itemized Table**: Lists line-item descriptions, quantities, unit prices, and row totals.

---

### Tab 3: Edit & Validate
1. **Field Correction Form**: Allows an operator to manually correct or adjust any parameter (Vendor, Invoice #, Dates, Financial amounts).
2. **Interactive Line Item Editor**: Add, remove, or modify item rows inline using Streamlit's interactive data grid.
3. **Save to Database**: Click **"💾 Save Validated Invoice to Database"** to commit the record to SQLite with status marked as `VALIDATED`.

---

### Tab 4: Database & Analytics
1. **KPI Dashboard**: View real-time aggregate statistics:
   - *Total Invoices Processed*
   - *Total Financial Expenditure*
   - *Average Invoice Value*
   - *Validation Pass Rate (%)*
2. **Search & Filters**: Search across invoices by vendor name, invoice number, or PO number, or filter by validation status.
3. **Export Center**:
   - **Download JSON**: Generates structured `invoices_export.json` with nested items.
   - **Download Summary CSV**: Generates `invoices_summary.csv` for spreadsheet analysis.
   - **Download Detailed Items CSV**: Generates flattened `invoice_items_detailed.csv` linking each line item to its parent invoice.
4. **Delete / Manage**: Select an invoice by ID to permanently remove it and its associated line items.

---

### Tab 5: Architecture & Guide
- Explains the complete Computer Vision and Document AI pipeline with Mermaid flowcharts.
- Reviews technical interview talking points and computer vision design decisions.
- Shows live system diagnostic JSON telemetry.
