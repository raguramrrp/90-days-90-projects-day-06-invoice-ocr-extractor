# 60–120 Second Portfolio Demonstration Script

**Project Title**: Automated Invoice Data Extraction & Structuring System  
**Target Audience**: Technical Recruiters, Hiring Managers, Hackathon Judges  
**Setup**: Run `run.bat` and open `http://localhost:8501`.

---

## Act 1: The Problem & The Solution (0:00 – 0:25)
> *"Hello! Businesses process thousands of invoices every month, and most accounts payable teams are still manually typing invoice numbers, dates, and amounts into their accounting software. This causes data entry errors, delayed vendor payments, and high operational costs.*
>
> *For Day 6 of my 90 Days Challenge, I built an Automated Invoice Data Extraction & Structuring System using Computer Vision, Tesseract OCR, and rule-based NLP to convert unstructured invoice scans and PDFs into mathematically validated, structured database records."*

---

## Act 2: Computer Vision & Live OCR Extraction (0:25 – 0:55)
> *(Action: Go to Sidebar, select sample `INV-2026-001_Apex_Hardware.png`, and click "⚡ Load & Process This Sample")*
>
> *"Here, our system ingests a hardware invoice. Let's look at the Visual Document Inspector:*
> - *First, our OpenCV pipeline converts the image to luminance grayscale, automatically deskews rotational tilt, suppresses camera noise with bilateral filtering, and applies Otsu binarization.*
> - *Next, Tesseract OCR runs in Page Segmentation Mode 4 to read across multi-column tables, generating word-level coordinate bounding boxes colored by confidence: green for high confidence, orange for medium, and red for low."*

---

## Act 3: Accounting Balance Validation & Human-in-the-Loop (0:55 – 1:25)
> *(Action: Switch to Tab 2: Extracted Data & Review)*
>
> *"Now let's look at the structured data. The system extracted the vendor name ('Apex Hardware Labs LLC'), invoice number, issue date, due date, terms, and individual itemized hardware rows.*
>
> *Crucially, instead of blindly trusting OCR output, our validator enforces strict financial accounting rules: it verifies that $\text{Subtotal} + \text{Tax} + \text{Shipping} - \text{Discount}$ equals the extracted Total Amount with zero discrepancy, certifying the invoice as VALIDATED with an EXCELLENT audit rating.*
>
> *(Action: Switch to Tab 3: Edit & Validate)*
> *If an edge-case invoice ever has a discrepancy, our human-in-the-loop review screen allows operators to tweak numbers or edit line items inline before committing."*

---

## Act 4: Relational Database & Multi-Format Export (1:25 – 1:50)
> *(Action: Switch to Tab 4: Database & Analytics)*
>
> *"Once validated, invoices are persisted into an SQLite database with cascading foreign keys between invoices and invoice items. The executive dashboard provides real-time analytics on total expenditure, average invoice values, and spend by vendor.*
>
> *Finally, with a single click, users can export structured JSON payloads or download clean CSV spreadsheets ready for ERP integration."*

---

## Closing Summary (1:50 – 2:00)
> *"The entire system is covered by an automated test suite of 27 unit and integration tests passing in under 3 seconds, runs completely locally on Windows, and demonstrates real-world document AI and FinTech automation."*
