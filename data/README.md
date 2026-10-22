# Dataset & Sample Invoices Documentation

## 1. Dataset Origin & Licensing
All invoice documents in `data/sample_invoices/` are **100% synthetically generated** for this project using ReportLab and pypdfium2.
- **Privacy & Compliance**: Contains zero personally identifiable information (PII), proprietary corporate data, or real financial account credentials.
- **License**: Public Domain / MIT Compatible. Free for benchmarking, demonstration, and automated test reproduction.

---

## 2. Included Sample Invoices
The bundled dataset covers 5 distinct business domains and financial structures:

| File Name | Vendor Name | Domain | Key Financial Fields | Total Amount |
| :--- | :--- | :--- | :--- | :---: |
| `INV-2026-001_Apex_Hardware.png/.pdf` | Apex Hardware Labs LLC | Hardware & Peripherals | 3 Line Items, Subtotal, 8% Tax, Shipping ($25.00) | **$1,531.60** |
| `INV-2026-002_CloudScale_Technologies.png/.pdf` | CloudScale Technologies Inc. | SaaS & Cloud Hosting | 3 Line Items, Startup Discount (-$100.00), 10% Tax | **$1,210.00** |
| `INV-2026-003_Quantum_Consulting.png/.pdf` | Quantum Consulting Partners LLP | Professional Services | Hourly Consulting Rates, Net 30, 5% Tax | **$5,512.50** |
| `INV-2026-004_Metro_Office_Supplies.png/.pdf` | Metro Office Supplies Co. | Office Supplies | PO Number (`PO-88421`), 3 Line Items, Tax, Shipping ($15.00) | **$454.56** |
| `INV-2026-005_CyberShield_Security.png/.pdf` | CyberShield Security Solutions | Cybersecurity Licenses | Software Seats, Vulnerability Scanner, 8% Tax | **$1,917.00** |

---

## 3. Regenerating Sample Files
To regenerate all sample PDFs and high-resolution PNG images from source specifications:
```cmd
.venv\Scripts\python.exe scripts\generate_sample_invoices.py
```
To seed the SQLite database with these sample invoices:
```cmd
.venv\Scripts\python.exe scripts\seed_database.py
```

---

## 4. Database Schema
Persisted records are stored in `data/invoices.db` with relational schema:
- **`invoices`**: Top-level invoice record with vendor, dates, totals, and audit status.
- **`invoice_items`**: Child table referencing `invoices(id)` via cascading foreign key.
