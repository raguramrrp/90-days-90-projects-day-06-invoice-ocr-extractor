"""Automated Invoice Data Extraction & Structuring System.

Streamlit web application for optical character recognition,
regex/heuristic field parsing, accounting balance validation, and SQLite persistence.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from PIL import Image
import streamlit as st

import config
from src.database.repository import InvoiceRepository
from src.exporter.csv_exporter import export_detailed_items_csv, export_summary_csv
from src.exporter.json_exporter import export_to_json
from src.ocr.engine import OCREngine
from src.ocr.pdf_processor import PDFProcessor
from src.parser.extractor import FieldExtractor
from src.validator.schema_validator import validate_invoice_payload

# Initialize Page Configuration
st.set_page_config(
    page_title="Invoice OCR Extractor | 90 Days Challenge",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for polished styling
st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #64748b;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
    }
    .badge-validated {
        background-color: #dcfce7;
        color: #15803d;
        padding: 0.25rem 0.6rem;
        border-radius: 6px;
        font-weight: 600;
    }
    .badge-discrepancy {
        background-color: #fee2e2;
        color: #b91c1c;
        padding: 0.25rem 0.6rem;
        border-radius: 6px;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def get_ocr_engine() -> OCREngine:
    """Cache OCR engine instance."""
    return OCREngine()


@st.cache_resource
def get_repository() -> InvoiceRepository:
    """Cache database repository instance."""
    return InvoiceRepository()


def init_session_state() -> None:
    """Initialize application session state variables."""
    if "current_file_name" not in st.session_state:
        st.session_state.current_file_name = None
    if "ocr_result" not in st.session_state:
        st.session_state.ocr_result = None
    if "extracted_data" not in st.session_state:
        st.session_state.extracted_data = None
    if "validation_report" not in st.session_state:
        st.session_state.validation_report = None
    if "active_tab" not in st.session_state:
        st.session_state.active_tab = 0


init_session_state()
engine = get_ocr_engine()
repo = get_repository()
diag = config.get_system_diagnostics()

# ==============================================================================
# SIDEBAR
# ==============================================================================
with st.sidebar:
    st.markdown("### 🧾 Invoice OCR System")
    st.caption("Day 6 — 90 Days Challenge")

    # Engine Status Badge
    if diag["ocr_available"]:
        st.success(f"🟢 **Tesseract Active** (v{diag['ocr_version']})")
    else:
        st.warning("🟡 **Tesseract Binary Not Detected**")
        st.caption("Fallback digital extraction & demo mode active.")

    st.markdown("---")
    st.markdown("#### 📁 Quick Demo Invoices")
    st.caption("Test immediately without searching for files:")

    sample_dir = config.BASE_DIR / "data" / "sample_invoices"
    sample_files = sorted(list(sample_dir.glob("*.png")))

    sample_options = ["None (Upload Custom)"] + [f.name for f in sample_files]
    selected_sample = st.selectbox("Select Sample Invoice", sample_options)

    if selected_sample != "None (Upload Custom)":
        sample_path = sample_dir / selected_sample
        if st.button("⚡ Load & Process This Sample", use_container_width=True, type="primary"):
            with st.spinner(f"Running OCR on {selected_sample}..."):
                res = engine.process_document(sample_path)
                ext = FieldExtractor.extract_all(res["raw_text"])
                ext["raw_text"] = res["raw_text"]
                ext["filename"] = selected_sample
                schema, report = validate_invoice_payload(ext)

                st.session_state.current_file_name = selected_sample
                st.session_state.ocr_result = res
                st.session_state.extracted_data = ext
                st.session_state.validation_report = report
                st.success(f"Processed {selected_sample} successfully!")

    st.markdown("---")
    st.markdown("#### ⚙️ Preprocessing Tuning")
    preproc_mode = st.selectbox(
        "Thresholding Mode",
        ["standard", "adaptive", "grayscale_only", "none"],
        index=0,
        help="Standard uses Otsu binarization. Adaptive handles uneven shadows or camera photos.",
    )
    auto_deskew = st.checkbox("Auto-Deskew (Straighten)", value=True)
    upscale_factor = st.slider("High-DPI Upscale Factor", 1.0, 2.5, 1.5, 0.25)

    st.markdown("---")
    st.caption("Portfolio Project | AI/DS & Computer Vision")


# ==============================================================================
# MAIN PAGE HEADER & NAVIGATION TABS
# ==============================================================================
st.markdown('<div class="main-title">Automated Invoice Data Extraction & Structuring</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">Extract vendor, dates, totals, and itemized tables from invoice images and PDFs using Computer Vision, Tesseract OCR, and Rule-Based NLP.</div>',
    unsafe_allow_html=True,
)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📤 Upload & Extract",
    "📊 Extracted Data & Review",
    "✏️ Edit & Validate",
    "🗄️ Database & Analytics",
    "ℹ️ Architecture & Guide",
])

# ==============================================================================
# TAB 1: UPLOAD & PROCESS
# ==============================================================================
with tab1:
    col_upload, col_preview = st.columns([1, 1], gap="large")

    with col_upload:
        st.markdown("#### 1. Upload Invoice Document")
        uploaded_file = st.file_uploader(
            "Drop invoice image or PDF file here",
            type=["png", "jpg", "jpeg", "tiff", "pdf"],
            help="Supports high-resolution scans, photos, or digital PDF invoices.",
        )

        if uploaded_file is not None:
            file_bytes = uploaded_file.read()
            filename = uploaded_file.name

            st.info(f"📄 Loaded `{filename}` ({len(file_bytes) / 1024:.1f} KB)")

            if st.button("🚀 Run OCR & Field Extraction", type="primary", use_container_width=True):
                with st.spinner("Processing image through Computer Vision pipeline..."):
                    res = engine.process_document(
                        file_bytes,
                        preprocess_mode=preproc_mode,
                        auto_deskew=auto_deskew,
                        upscale_factor=upscale_factor,
                    )
                    ext = FieldExtractor.extract_all(res["raw_text"])
                    ext["raw_text"] = res["raw_text"]
                    ext["filename"] = filename
                    schema, report = validate_invoice_payload(ext)

                    st.session_state.current_file_name = filename
                    st.session_state.ocr_result = res
                    st.session_state.extracted_data = ext
                    st.session_state.validation_report = report

                    st.success("Extraction complete! Check the 'Extracted Data & Review' tab.")

        elif st.session_state.current_file_name:
            st.success(f"Current active document: **{st.session_state.current_file_name}**")

        st.markdown("---")
        st.markdown("#### 💡 How It Works")
        st.markdown(
            """
            1. **Document Ingestion**: Accepts multi-format image files (PNG/JPG) or multi-page PDFs.
            2. **Computer Vision Enhancement**: Converts to luminance grayscale, deskews rotation, suppresses noise with bilateral filtering, and applies Otsu binarization.
            3. **Optical Character Recognition**: Tesseract engine extracts raw text and spatial bounding boxes with confidence scoring.
            4. **Entity & Regex Extraction**: Parses vendor names, invoice numbers, dates, currency, and line items.
            5. **Accounting Balance Validation**: Mathematically checks whether `Subtotal + Tax + Shipping - Discount == Total Amount`.
            """
        )

    with col_preview:
        st.markdown("#### 2. Visual Document Inspector")
        if st.session_state.ocr_result:
            res = st.session_state.ocr_result

            preview_choice = st.radio(
                "Display Mode",
                ["Original Document", "Preprocessed Binary", "OCR Bounding Boxes", "Raw Text"],
                horizontal=True,
            )

            if preview_choice == "Original Document":
                st.image(res["original_preview"], caption=f"Original Document: {st.session_state.current_file_name}", use_container_width=True)
            elif preview_choice == "Preprocessed Binary":
                st.image(res["preprocessed_image"], caption="OpenCV Preprocessed Image (Binarized & Deskewed)", use_container_width=True)
            elif preview_choice == "OCR Bounding Boxes":
                st.image(res["annotated_image"], caption="Detected Word Bounding Boxes (Green >= 80%, Orange >= 50%, Red < 50%)", use_container_width=True)
            else:
                st.text_area("Extracted Raw Text", res["raw_text"], height=420)

            # Metadata telemetry
            st.caption(
                f"⏱️ **Processing Time**: {res['processing_time_sec']}s | "
                f"🎯 **OCR Confidence**: {res['mean_confidence']}% | "
                f"📐 **Deskew Angle**: {res['preprocessing_meta'].get('skew_angle', 0.0)}°"
            )
        else:
            st.info("Upload an invoice or select a quick demo sample from the sidebar to inspect the visual pipeline.")


# ==============================================================================
# TAB 2: EXTRACTED DATA & REVIEW
# ==============================================================================
with tab2:
    if not st.session_state.extracted_data:
        st.info("No invoice data has been extracted yet. Please upload a file or choose a sample in Tab 1.")
    else:
        ext = st.session_state.extracted_data
        report = st.session_state.validation_report
        math_audit = report.get("math_audit", {})

        # Validation Grade Banner
        if report["grade"] == "EXCELLENT":
            st.success("✅ **Validation Status: VALIDATED** — Accounting reconciliation verified with 0 discrepancy.")
        elif report["grade"] == "GOOD":
            st.warning("⚠️ **Validation Status: VERIFIED WITH WARNINGS** — Balance matches, but review minor warnings.")
        else:
            st.error(f"❌ **Validation Status: DISCREPANCY DETECTED** — Discrepancy of {math_audit.get('discrepancy', 0.0):+.2f}.")

        # Top Metadata Columns
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Vendor Name", ext.get("vendor_name", "Unknown"))
            st.caption(f"Confidence: {ext.get('field_confidences', {}).get('vendor_name', 0.0)*100:.0f}%")
        with c2:
            st.metric("Invoice Number", ext.get("invoice_number", "N/A"))
            st.caption(f"Confidence: {ext.get('field_confidences', {}).get('invoice_number', 0.0)*100:.0f}%")
        with c3:
            st.metric("Invoice Date", ext.get("invoice_date") or "N/A")
            st.caption(f"Confidence: {ext.get('field_confidences', {}).get('invoice_date', 0.0)*100:.0f}%")
        with c4:
            st.metric("Due Date", ext.get("due_date") or "N/A")
            st.caption(f"Terms: {ext.get('payment_terms') or 'Standard'}")

        st.markdown("---")

        # Financial Breakdown
        st.markdown("#### 💰 Financial Breakdown & Balance Equation")
        f1, f2, f3, f4, f5 = st.columns(5)
        curr = ext.get("currency", "USD")

        with f1:
            st.metric("Subtotal", f"{curr} {ext.get('subtotal', 0.0):,.2f}")
        with f2:
            st.metric("Tax (VAT/GST)", f"{curr} {ext.get('tax_amount', 0.0):,.2f}")
        with f3:
            st.metric("Shipping", f"{curr} {ext.get('shipping_amount', 0.0):,.2f}")
        with f4:
            st.metric("Discount", f"-{curr} {ext.get('discount_amount', 0.0):,.2f}")
        with f5:
            st.metric("Grand Total", f"{curr} {ext.get('total_amount', 0.0):,.2f}")

        # Math Verification Summary Box
        st.markdown("##### 🧮 Accounting Reconciliation Check")
        for msg in math_audit.get("messages", []):
            if "Total mismatch" in msg or "differs" in msg:
                st.markdown(f"- 🔴 {msg}")
            else:
                st.markdown(f"- 🟢 {msg}")

        st.markdown("---")

        # Line Items Table
        st.markdown("#### 📦 Itemized Line Items")
        line_items = ext.get("line_items", [])
        if line_items:
            df_items = pd.DataFrame(line_items)
            df_items.columns = ["Description", "Quantity", "Unit Price", "Total Amount"]
            st.dataframe(df_items, use_container_width=True, hide_index=True)
            st.caption(f"Total Line Items: {len(line_items)} | Sum: {curr} {sum(i.get('amount', 0.0) for i in line_items):,.2f}")
        else:
            st.info("No individual line items parsed from document text.")


# ==============================================================================
# TAB 3: EDIT & VALIDATE
# ==============================================================================
with tab3:
    if not st.session_state.extracted_data:
        st.info("No data available to edit. Please process an invoice first.")
    else:
        st.markdown("#### ✏️ Human-in-the-Loop Review & Field Adjustment")
        st.caption("Review extracted parameters, make corrections, and commit validated record to SQLite database.")

        ext = st.session_state.extracted_data

        with st.form("invoice_edit_form"):
            col_e1, col_e2 = st.columns(2)

            with col_e1:
                edit_vendor = st.text_input("Vendor Name", value=ext.get("vendor_name", ""))
                edit_inv_no = st.text_input("Invoice Number", value=ext.get("invoice_number", ""))
                edit_date = st.text_input("Invoice Date (YYYY-MM-DD)", value=ext.get("invoice_date") or "")
                edit_due = st.text_input("Due Date (YYYY-MM-DD)", value=ext.get("due_date") or "")
                edit_currency = st.text_input("Currency", value=ext.get("currency", "USD"))
                edit_po = st.text_input("PO Number", value=ext.get("po_number") or "")

            with col_e2:
                edit_subtotal = st.number_input("Subtotal", value=float(ext.get("subtotal", 0.0)), step=10.0)
                edit_tax = st.number_input("Tax Amount", value=float(ext.get("tax_amount", 0.0)), step=5.0)
                edit_ship = st.number_input("Shipping Amount", value=float(ext.get("shipping_amount", 0.0)), step=5.0)
                edit_disc = st.number_input("Discount Amount", value=float(ext.get("discount_amount", 0.0)), step=5.0)
                edit_total = st.number_input("Total Amount", value=float(ext.get("total_amount", 0.0)), step=10.0)
                edit_terms = st.text_input("Payment Terms", value=ext.get("payment_terms") or "")

            st.markdown("##### Edit Line Items")
            existing_items = ext.get("line_items", [])
            df_edit_items = pd.DataFrame(existing_items if existing_items else [{"description": "Item 1", "quantity": 1.0, "unit_price": edit_total, "amount": edit_total}])

            edited_df = st.data_editor(
                df_edit_items,
                num_rows="dynamic",
                use_container_width=True,
                key="items_editor",
            )

            submit_save = st.form_submit_button("💾 Save Validated Invoice to Database", type="primary")

            if submit_save:
                # Compile updated invoice
                updated_items = edited_df.to_dict(orient="records")
                updated_invoice = {
                    "filename": ext.get("filename") or st.session_state.current_file_name,
                    "vendor_name": edit_vendor,
                    "invoice_number": edit_inv_no,
                    "invoice_date": edit_date or None,
                    "due_date": edit_due or None,
                    "currency": edit_currency,
                    "subtotal": edit_subtotal,
                    "tax_amount": edit_tax,
                    "shipping_amount": edit_ship,
                    "discount_amount": edit_disc,
                    "total_amount": edit_total,
                    "payment_terms": edit_terms or None,
                    "po_number": edit_po or None,
                    "overall_confidence": ext.get("overall_confidence", 0.9),
                    "validation_status": "VALIDATED",
                    "raw_text": ext.get("raw_text", ""),
                }

                inv_id = repo.save_invoice(
                    updated_invoice,
                    items=updated_items,
                    filename=updated_invoice["filename"],
                )
                st.success(f"🎉 Invoice successfully saved with ID #{inv_id} into SQLite database!")


# ==============================================================================
# TAB 4: DATABASE & EXPORT
# ==============================================================================
with tab4:
    st.markdown("#### 🗄️ Database Records & Financial Analytics")

    # Aggregate Analytics
    analytics = repo.get_analytics_summary()
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Total Invoices", analytics["total_invoices"])
    with m2:
        st.metric("Total Expenditure", f"${analytics['total_spend']:,.2f}")
    with m3:
        st.metric("Average Invoice", f"${analytics['avg_amount']:,.2f}")
    with m4:
        validated_count = analytics["status_breakdown"].get("VALIDATED", 0)
        pass_rate = (validated_count / analytics["total_invoices"] * 100) if analytics["total_invoices"] > 0 else 100
        st.metric("Validation Rate", f"{pass_rate:.1f}%")

    st.markdown("---")

    # Filter Controls
    f_col1, f_col2, f_col3 = st.columns([2, 1, 1])
    with f_col1:
        search_query = st.text_input("🔍 Search by Vendor, Invoice # or PO", placeholder="e.g. Apex Hardware or INV-2026")
    with f_col2:
        vendor_filter = st.selectbox("Filter Vendor", ["All"] + [v["vendor_name"] for v in analytics["top_vendors"]])
    with f_col3:
        status_filter = st.selectbox("Filter Status", ["All", "VALIDATED", "PENDING", "DISCREPANCY"])

    # Fetch Invoices
    db_invoices = repo.get_invoices(
        search_query=search_query,
        vendor=vendor_filter,
        status=status_filter,
    )

    if db_invoices:
        df_db = pd.DataFrame(db_invoices)
        display_cols = ["id", "vendor_name", "invoice_number", "invoice_date", "currency", "total_amount", "validation_status", "created_at"]
        st.dataframe(df_db[display_cols], use_container_width=True, hide_index=True)

        st.markdown("#### 📥 Export Data Center")
        exp_c1, exp_c2, exp_c3 = st.columns(3)

        with exp_c1:
            json_data = export_to_json(db_invoices)
            st.download_button(
                "📥 Download JSON (All Invoices)",
                data=json_data,
                file_name="invoices_export.json",
                mime="application/json",
                use_container_width=True,
            )

        with exp_c2:
            summary_csv = export_summary_csv(db_invoices)
            st.download_button(
                "📊 Download Summary CSV",
                data=summary_csv,
                file_name="invoices_summary.csv",
                mime="text/csv",
                use_container_width=True,
            )

        with exp_c3:
            # Attach line items for detailed CSV
            detailed_list = []
            for inv in db_invoices:
                full_inv = repo.get_invoice_by_id(inv["id"])
                if full_inv:
                    detailed_list.append(full_inv)
            detailed_csv = export_detailed_items_csv(detailed_list)
            st.download_button(
                "📋 Download Detailed Items CSV",
                data=detailed_csv,
                file_name="invoice_items_detailed.csv",
                mime="text/csv",
                use_container_width=True,
            )

        st.markdown("---")
        st.markdown("#### 🗑️ Delete / Manage Record")
        del_col1, del_col2 = st.columns([3, 1])
        with del_col1:
            del_id = st.selectbox("Select Invoice ID to delete", [inv["id"] for inv in db_invoices], format_func=lambda x: f"Invoice #{x}")
        with del_col2:
            if st.button("Delete Record", type="secondary"):
                if repo.delete_invoice(del_id):
                    st.success(f"Invoice #{del_id} deleted.")
                    st.rerun()

    else:
        st.info("No matching records found in SQLite database. Save an invoice from Tab 3 or load demo invoices.")


# ==============================================================================
# TAB 5: ARCHITECTURE & GUIDE
# ==============================================================================
with tab5:
    st.markdown("#### 📐 System Architecture & Computer Vision Pipeline")

    st.markdown(
        """
        ```mermaid
        flowchart LR
            A[Invoice Image / PDF] --> B[PDF Processor / Rasterizer]
            B --> C[OpenCV Preprocessing]
            subgraph Preprocessing [Computer Vision Pipeline]
                C1[Grayscale Luminance] --> C2[Bilateral Denoising]
                C2 --> C3[MinAreaRect Deskewing]
                C3 --> C4[Otsu Adaptive Binarization]
            end
            C --> Preprocessing
            Preprocessing --> D[Tesseract OCR Engine]
            D --> E[Multi-Pattern Regex & NLP]
            subgraph Extraction [Entity & Field Extraction]
                E1[Vendor Heuristics]
                E2[Invoice # & PO]
                E3[Date Parser]
                E4[Line Item Parser]
            end
            E --> Extraction
            Extraction --> F[Accounting Math Validator]
            F --> G[Pydantic Schema Validation]
            G --> H[(SQLite Database)]
            G --> I[JSON / CSV Exporter]
        ```
        """
    )

    st.markdown("#### 💼 Interview Value & Key Concepts")
    st.markdown(
        """
        - **Computer Vision Preprocessing**: Demonstrates practical knowledge of grayscale conversion, bilateral edge-preserving smoothing, Otsu binarization, and affine transformation for deskewing.
        - **OCR Integration**: Interfaces directly with Tesseract OCR (PSM 4/3) to extract both text strings and word-level coordinate bounding boxes with confidence scoring.
        - **Information Extraction (IE)**: Employs multi-stage regular expressions, right-to-left reverse tokenization for table rows, and heuristic entity filtering to separate vendor branding from document labels.
        - **Financial Verification**: Enforces rigorous business domain rules (`Subtotal + Tax + Shipping - Discount == Total Amount`) rather than blindly trusting OCR strings.
        - **Relational Data Persistence**: SQLite schema enforcing cascading foreign keys between `invoices` and `invoice_items` with structured JSON/CSV export capabilities.
        """
    )

    st.markdown("---")
    st.markdown("#### 🔧 System Diagnostics")
    st.json(diag)
