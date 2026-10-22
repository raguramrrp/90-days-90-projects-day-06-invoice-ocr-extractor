"""Automated Invoice Data Extraction & Structuring System.

Expert FinTech & Document Intelligence UI for optical character recognition,
accounting reconciliation, and relational ledger persistence.
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
    page_title="Invoice Intelligence Suite | Ledger AI",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom High-End FinTech Design System (Nordic Precision / Warm Editorial Neo-Bank)
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #1C1917;
    }

    /* Top Brand Header */
    .brand-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding-bottom: 1.25rem;
        margin-bottom: 1.5rem;
        border-bottom: 1px solid #E7E5E4;
    }
    .brand-title {
        font-size: 1.85rem;
        font-weight: 700;
        letter-spacing: -0.03em;
        color: #0F172A;
        margin: 0;
        line-height: 1.2;
    }
    .brand-subtitle {
        font-size: 0.95rem;
        color: #78716C;
        margin-top: 0.25rem;
    }
    .brand-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        background: #F0FDF4;
        color: #166534;
        border: 1px solid #BBF7D0;
        padding: 0.35rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.02em;
        text-transform: uppercase;
    }

    /* Metric & Surface Cards */
    .fintech-card {
        background: #FFFFFF;
        border: 1px solid #E7E5E4;
        border-radius: 10px;
        padding: 1.15rem 1.25rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
        margin-bottom: 1rem;
    }
    .card-label {
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #78716C;
        margin-bottom: 0.4rem;
    }
    .card-value {
        font-size: 1.45rem;
        font-weight: 700;
        color: #0F172A;
        font-family: 'JetBrains Mono', monospace;
        letter-spacing: -0.02em;
    }
    .card-subtext {
        font-size: 0.78rem;
        color: #A8A29E;
        margin-top: 0.25rem;
    }

    /* Accounting Equation Visualizer */
    .equation-bar {
        background: #FFFFFF;
        border: 1px solid #E7E5E4;
        border-radius: 12px;
        padding: 1rem 1.5rem;
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 0.75rem;
        margin: 1.25rem 0;
        box-shadow: 0 1px 4px rgba(0,0,0,0.02);
    }
    .equation-chip {
        background: #F5F5F4;
        border: 1px solid #E7E5E4;
        border-radius: 8px;
        padding: 0.45rem 0.85rem;
        font-size: 0.85rem;
    }
    .chip-label {
        color: #78716C;
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        display: block;
    }
    .chip-val {
        font-weight: 600;
        font-family: 'JetBrains Mono', monospace;
        color: #1C1917;
    }
    .equation-symbol {
        font-size: 1.1rem;
        font-weight: 700;
        color: #A8A29E;
    }
    .equation-total {
        background: #F0FDF4;
        border: 1px solid #BBF7D0;
        border-radius: 8px;
        padding: 0.45rem 0.95rem;
    }
    .equation-total .chip-label {
        color: #166534;
    }
    .equation-total .chip-val {
        color: #14532D;
        font-size: 1rem;
    }

    /* Status Pills */
    .pill-success {
        background: #ECFDF5;
        color: #065F46;
        border: 1px solid #A7F3D0;
        padding: 0.25rem 0.65rem;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.8rem;
        display: inline-block;
    }
    .pill-warning {
        background: #FFFBEB;
        color: #92400E;
        border: 1px solid #FDE68A;
        padding: 0.25rem 0.65rem;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.8rem;
        display: inline-block;
    }
    .pill-danger {
        background: #FFF1F2;
        color: #9F1239;
        border: 1px solid #FECDD3;
        padding: 0.25rem 0.65rem;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.8rem;
        display: inline-block;
    }

    /* Tab Styling */
    div[data-baseweb="tab-list"] {
        gap: 0.5rem;
        border-bottom: 1px solid #E7E5E4;
        padding-bottom: 0.25rem;
    }
    div[data-baseweb="tab"] {
        font-size: 0.92rem;
        font-weight: 600;
        padding: 0.6rem 1.1rem;
        border-radius: 8px;
        color: #78716C;
    }
    div[data-baseweb="tab"][aria-selected="true"] {
        background: #059669 !important;
        color: #FFFFFF !important;
    }

    /* Buttons */
    .stButton>button[kind="primary"] {
        background-color: #059669;
        border: none;
        color: white;
        font-weight: 600;
        border-radius: 8px;
        padding: 0.55rem 1.25rem;
        box-shadow: 0 1px 2px rgba(5, 150, 105, 0.2);
    }
    .stButton>button[kind="primary"]:hover {
        background-color: #047857;
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
    """Initialize session state variables."""
    if "current_file_name" not in st.session_state:
        st.session_state.current_file_name = None
    if "ocr_result" not in st.session_state:
        st.session_state.ocr_result = None
    if "extracted_data" not in st.session_state:
        st.session_state.extracted_data = None
    if "validation_report" not in st.session_state:
        st.session_state.validation_report = None


init_session_state()
engine = get_ocr_engine()
repo = get_repository()
diag = config.get_system_diagnostics()

# ==============================================================================
# SIDEBAR: DOCUMENT SELECTION & ENGINE STATUS
# ==============================================================================
with st.sidebar:
    st.markdown("### 🧾 Invoice Intelligence")
    st.caption("Commercial Document Extraction & Audit Engine")

    # Engine Status Pill
    if diag["ocr_available"]:
        st.markdown(
            f"""
            <div style="background:#F0FDF4; border:1px solid #BBF7D0; border-radius:8px; padding:0.6rem 0.8rem; margin-bottom:1rem;">
                <span style="color:#166534; font-weight:600; font-size:0.82rem;">● OCR Engine Online</span>
                <div style="color:#15803D; font-size:0.75rem; margin-top:2px;">Tesseract v{diag['ocr_version']} (PSM 4 Table Mode)</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div style="background:#FFFBEB; border:1px solid #FDE68A; border-radius:8px; padding:0.6rem 0.8rem; margin-bottom:1rem;">
                <span style="color:#92400E; font-weight:600; font-size:0.82rem;">⚠ OCR Engine Fallback</span>
                <div style="color:#B45309; font-size:0.75rem; margin-top:2px;">Digital extraction & simulation active</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("#### 📁 Curated Sample Invoices")
    st.caption("Load verified enterprise sample documents instantly:")

    sample_dir = config.BASE_DIR / "data" / "sample_invoices"
    sample_files = sorted(list(sample_dir.glob("*.png")))
    sample_options = ["None (Upload Custom)"] + [f.name for f in sample_files]
    selected_sample = st.selectbox("Select Invoice", sample_options)

    if selected_sample != "None (Upload Custom)":
        sample_path = sample_dir / selected_sample
        if st.button("⚡ Ingest Sample Document", use_container_width=True, type="primary"):
            with st.spinner(f"Extracting & auditing {selected_sample}..."):
                res = engine.process_document(sample_path)
                ext = FieldExtractor.extract_all(res["raw_text"])
                ext["raw_text"] = res["raw_text"]
                ext["filename"] = selected_sample
                schema, report = validate_invoice_payload(ext)

                st.session_state.current_file_name = selected_sample
                st.session_state.ocr_result = res
                st.session_state.extracted_data = ext
                st.session_state.validation_report = report
                st.toast(f"Loaded {selected_sample}", icon="✅")

    st.markdown("---")
    st.markdown("#### ⚙️ Computer Vision Tuning")
    preproc_mode = st.selectbox(
        "Threshold Filter",
        ["standard", "adaptive", "grayscale_only", "none"],
        index=0,
        help="Standard uses Otsu global thresholding. Adaptive Gaussian compensates for mobile camera shadows.",
    )
    auto_deskew = st.checkbox("Auto-Deskew (Straighten tilt)", value=True)
    upscale_factor = st.slider("DPI Rescale Factor", 1.0, 2.5, 1.5, 0.25, help="Magnifies small receipt typography.")

    st.markdown("---")
    with st.expander("ℹ️ System Engine & Diagnostic Info"):
        st.caption(f"**Database**: `{diag['database_path']}`")
        st.caption(f"**Tesseract Path**: `{diag['tesseract_executable']}`")
        st.caption(f"**Allowed Formats**: {', '.join(diag['allowed_extensions'])}")


# ==============================================================================
# MAIN WORKSPACE HEADER
# ==============================================================================
st.markdown(
    """
    <div class="brand-container">
        <div>
            <h1 class="brand-title">Invoice Intelligence & Reconciliation Suite</h1>
            <div class="brand-subtitle">Automated Document Ingestion, Information Extraction, and Accounting Verification</div>
        </div>
        <div>
            <span class="brand-badge">● Production Mode</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

tab_ingest, tab_reconcile, tab_edit, tab_ledger = st.tabs([
    "📄 Document Ingestion",
    "⚖️ Financial Reconciliation",
    "✍️ Operator Review & Edit",
    "📊 Ledger & Audit Exports",
])

# ==============================================================================
# TAB 1: DOCUMENT INGESTION
# ==============================================================================
with tab_ingest:
    col_up, col_view = st.columns([1, 1], gap="large")

    with col_up:
        st.markdown("#### Document Input")
        uploaded_file = st.file_uploader(
            "Upload invoice scan, photograph, or PDF file",
            type=["png", "jpg", "jpeg", "tiff", "pdf"],
            help="Accepts high-resolution scanned documents, smartphone captures, and multi-page vector PDFs.",
        )

        if uploaded_file is not None:
            file_bytes = uploaded_file.read()
            filename = uploaded_file.name

            st.markdown(
                f"""
                <div style="background:#F5F5F4; border:1px solid #E7E5E4; border-radius:8px; padding:0.6rem 0.9rem; margin:0.8rem 0;">
                    <span style="font-weight:600; font-size:0.85rem; color:#1C1917;">📄 Selected File:</span>
                    <span style="font-family:'JetBrains Mono', monospace; font-size:0.82rem; color:#059669;"> {filename}</span>
                    <span style="font-size:0.75rem; color:#78716C;"> ({len(file_bytes)/1024:.1f} KB)</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.button("🚀 Execute OCR & Extraction Pipeline", type="primary", use_container_width=True):
                with st.spinner("Executing Computer Vision & Character Recognition Pipeline..."):
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
                    st.toast("Extraction & Validation Successful!", icon="🎉")

        elif st.session_state.current_file_name:
            st.markdown(
                f"""
                <div style="background:#F0FDF4; border:1px solid #BBF7D0; border-radius:8px; padding:0.6rem 0.9rem; margin-bottom:1rem;">
                    <span style="font-weight:600; font-size:0.85rem; color:#166534;">Active Document:</span>
                    <span style="font-family:'JetBrains Mono', monospace; font-size:0.82rem; color:#15803D;"> {st.session_state.current_file_name}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown(
            """
            <div class="fintech-card" style="margin-top:1.5rem;">
                <div class="card-label">Pipeline Operational Flow</div>
                <div style="font-size:0.84rem; color:#57534E; line-height:1.6;">
                    <b>1. Ingestion:</b> Multi-format raster & PDF parsing via pypdfium2.<br>
                    <b>2. Preprocessing:</b> Bilateral smoothing, Otsu binarization, and auto-deskewing.<br>
                    <b>3. Recognition:</b> Tesseract OCR with spatial bounding boxes and word confidence scoring.<br>
                    <b>4. Extraction:</b> Multi-pattern regex & reverse-token table row parsing.<br>
                    <b>5. Audit:</b> Mathematical verification of Subtotal + Tax + Shipping - Discount = Total.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_view:
        st.markdown("#### Document Visual Inspector")
        if st.session_state.ocr_result:
            res = st.session_state.ocr_result

            preview_choice = st.radio(
                "Inspector Mode",
                ["Original Document", "Binary Enhancement", "OCR Word Bounding Boxes", "Raw Character Stream"],
                horizontal=True,
            )

            if preview_choice == "Original Document":
                st.image(res["original_preview"], caption=f"Source Document: {st.session_state.current_file_name}", use_container_width=True)
            elif preview_choice == "Binary Enhancement":
                st.image(res["preprocessed_image"], caption="Deskewed & Binarized Preprocessed Stream", use_container_width=True)
            elif preview_choice == "OCR Word Bounding Boxes":
                st.image(res["annotated_image"], caption="Spatial Confidence Overlay (Green: >=80%, Orange: 50-79%, Red: <50%)", use_container_width=True)
            else:
                st.text_area("Extracted Character Stream", res["raw_text"], height=440)

            # Telemetry Metrics
            t1, t2, t3 = st.columns(3)
            with t1:
                st.caption(f"⏱️ **Runtime**: `{res['processing_time_sec']}s`")
            with t2:
                st.caption(f"🎯 **OCR Confidence**: `{res['mean_confidence']}%`")
            with t3:
                st.caption(f"📐 **Tilt Adjustment**: `{res['preprocessing_meta'].get('skew_angle', 0.0)}°`")
        else:
            st.info("Upload an invoice or choose a sample in the sidebar to view live visual processing.")


# ==============================================================================
# TAB 2: FINANCIAL RECONCILIATION
# ==============================================================================
with tab_reconcile:
    if not st.session_state.extracted_data:
        st.info("No document currently loaded. Ingest an invoice in Tab 1 to inspect financial reconciliation.")
    else:
        ext = st.session_state.extracted_data
        report = st.session_state.validation_report
        math_audit = report.get("math_audit", {})
        curr = ext.get("currency", "USD")

        # Top Validation Status Bar
        if report["grade"] == "EXCELLENT":
            st.markdown(
                """
                <div style="background:#ECFDF5; border:1px solid #A7F3D0; border-radius:10px; padding:0.9rem 1.25rem; margin-bottom:1.25rem; display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <span style="font-weight:700; color:#065F46; font-size:0.95rem;">✓ RECONCILIATION CERTIFIED (Grade: EXCELLENT)</span>
                        <div style="color:#047857; font-size:0.82rem; margin-top:2px;">All mathematical formulas balance with exact $0.00 discrepancy.</div>
                    </div>
                    <span class="pill-success">Status: VALIDATED</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        elif report["grade"] == "GOOD":
            st.markdown(
                """
                <div style="background:#FFFBEB; border:1px solid #FDE68A; border-radius:10px; padding:0.9rem 1.25rem; margin-bottom:1.25rem; display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <span style="font-weight:700; color:#92400E; font-size:0.95rem;">⚠ RECONCILIATION VERIFIED WITH WARNINGS (Grade: GOOD)</span>
                        <div style="color:#B45309; font-size:0.82rem; margin-top:2px;">Financial balance equations match, but review non-critical fields.</div>
                    </div>
                    <span class="pill-warning">Status: VERIFIED</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
                <div style="background:#FFF1F2; border:1px solid #FECDD3; border-radius:10px; padding:0.9rem 1.25rem; margin-bottom:1.25rem; display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <span style="font-weight:700; color:#9F1239; font-size:0.95rem;">✕ DISCREPANCY DETECTED (Grade: NEEDS_REVIEW)</span>
                        <div style="color:#BE123C; font-size:0.82rem; margin-top:2px;">Extracted total differs by {math_audit.get('discrepancy', 0.0):+.2f} from calculated sum.</div>
                    </div>
                    <span class="pill-danger">Status: DISCREPANCY</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Entity Cards
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(
                f"""
                <div class="fintech-card">
                    <div class="card-label">Vendor Entity</div>
                    <div class="card-value" style="font-size:1.15rem; font-family:'Inter',sans-serif;">{ext.get('vendor_name', 'Unknown')}</div>
                    <div class="card-subtext">Confidence: {ext.get('field_confidences', {}).get('vendor_name', 0.0)*100:.0f}%</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                f"""
                <div class="fintech-card">
                    <div class="card-label">Invoice Number</div>
                    <div class="card-value" style="font-size:1.15rem;">{ext.get('invoice_number', 'N/A')}</div>
                    <div class="card-subtext">PO Reference: {ext.get('po_number') or 'None'}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c3:
            st.markdown(
                f"""
                <div class="fintech-card">
                    <div class="card-label">Issue Date</div>
                    <div class="card-value" style="font-size:1.15rem;">{ext.get('invoice_date') or 'N/A'}</div>
                    <div class="card-subtext">Confidence: {ext.get('field_confidences', {}).get('invoice_date', 0.0)*100:.0f}%</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c4:
            st.markdown(
                f"""
                <div class="fintech-card">
                    <div class="card-label">Due Date & Terms</div>
                    <div class="card-value" style="font-size:1.15rem;">{ext.get('due_date') or 'N/A'}</div>
                    <div class="card-subtext">Terms: {ext.get('payment_terms') or 'Due upon receipt'}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Accounting Equation Formula Bar
        st.markdown(
            f"""
            <div class="equation-bar">
                <div class="equation-chip">
                    <span class="chip-label">Subtotal</span>
                    <span class="chip-val">{curr} {ext.get('subtotal', 0.0):,.2f}</span>
                </div>
                <span class="equation-symbol">+</span>
                <div class="equation-chip">
                    <span class="chip-label">Tax (VAT/GST)</span>
                    <span class="chip-val">{curr} {ext.get('tax_amount', 0.0):,.2f}</span>
                </div>
                <span class="equation-symbol">+</span>
                <div class="equation-chip">
                    <span class="chip-label">Shipping</span>
                    <span class="chip-val">{curr} {ext.get('shipping_amount', 0.0):,.2f}</span>
                </div>
                <span class="equation-symbol">-</span>
                <div class="equation-chip">
                    <span class="chip-label">Discount</span>
                    <span class="chip-val">{curr} {ext.get('discount_amount', 0.0):,.2f}</span>
                </div>
                <span class="equation-symbol">=</span>
                <div class="equation-total">
                    <span class="chip-label">Total Amount Due</span>
                    <span class="chip-val">{curr} {ext.get('total_amount', 0.0):,.2f}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Itemized Line Items Table
        st.markdown("#### Itemized Line Items")
        line_items = ext.get("line_items", [])
        if line_items:
            df_items = pd.DataFrame(line_items)
            df_items.columns = ["Description", "Quantity", "Unit Price", "Total Amount"]
            st.dataframe(df_items, use_container_width=True, hide_index=True)
            st.caption(f"Line Item Count: {len(line_items)} | Sum: {curr} {sum(i.get('amount', 0.0) for i in line_items):,.2f}")
        else:
            st.info("No individual line items parsed from document text.")


# ==============================================================================
# TAB 3: OPERATOR REVIEW & EDIT
# ==============================================================================
with tab3:
    if not st.session_state.extracted_data:
        st.info("No document loaded. Extract an invoice first to review or edit fields.")
    else:
        st.markdown("#### Human-in-the-Loop Review & Field Overrides")
        st.caption("Adjust recognized parameters and commit confirmed records to the relational SQLite ledger.")

        ext = st.session_state.extracted_data

        with st.form("invoice_edit_form"):
            col_e1, col_e2 = st.columns(2)

            with col_e1:
                edit_vendor = st.text_input("Vendor Entity Name", value=ext.get("vendor_name", ""))
                edit_inv_no = st.text_input("Invoice Identifier / Number", value=ext.get("invoice_number", ""))
                edit_date = st.text_input("Invoice Date (YYYY-MM-DD)", value=ext.get("invoice_date") or "")
                edit_due = st.text_input("Payment Due Date (YYYY-MM-DD)", value=ext.get("due_date") or "")
                edit_currency = st.text_input("Currency Code", value=ext.get("currency", "USD"))
                edit_po = st.text_input("PO Reference Number", value=ext.get("po_number") or "")

            with col_e2:
                edit_subtotal = st.number_input("Subtotal Amount", value=float(ext.get("subtotal", 0.0)), step=10.0)
                edit_tax = st.number_input("Tax / VAT Amount", value=float(ext.get("tax_amount", 0.0)), step=5.0)
                edit_ship = st.number_input("Shipping & Freight", value=float(ext.get("shipping_amount", 0.0)), step=5.0)
                edit_disc = st.number_input("Discount Deductions", value=float(ext.get("discount_amount", 0.0)), step=5.0)
                edit_total = st.number_input("Final Grand Total", value=float(ext.get("total_amount", 0.0)), step=10.0)
                edit_terms = st.text_input("Payment Credit Terms", value=ext.get("payment_terms") or "")

            st.markdown("##### Line Items Grid")
            existing_items = ext.get("line_items", [])
            df_edit_items = pd.DataFrame(
                existing_items if existing_items else [
                    {"description": "Standard Item", "quantity": 1.0, "unit_price": edit_total, "amount": edit_total}
                ]
            )

            edited_df = st.data_editor(
                df_edit_items,
                num_rows="dynamic",
                use_container_width=True,
                key="items_editor",
            )

            submit_save = st.form_submit_button("💾 Commit Validated Invoice to Ledger", type="primary")

            if submit_save:
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
                    "overall_confidence": ext.get("overall_confidence", 0.95),
                    "validation_status": "VALIDATED",
                    "raw_text": ext.get("raw_text", ""),
                }

                inv_id = repo.save_invoice(
                    updated_invoice,
                    items=updated_items,
                    filename=updated_invoice["filename"],
                )
                st.success(f"🎉 Successfully persisted Invoice Record #{inv_id} to SQLite Ledger!")


# ==============================================================================
# TAB 4: LEDGER & AUDIT EXPORTS
# ==============================================================================
with tab_ledger:
    st.markdown("#### Enterprise Invoices Ledger & Analytics")

    # Executive Analytics Bar
    analytics = repo.get_analytics_summary()
    a1, a2, a3, a4 = st.columns(4)

    with a1:
        st.markdown(
            f"""
            <div class="fintech-card">
                <div class="card-label">Total Invoices Logged</div>
                <div class="card-value">{analytics['total_invoices']}</div>
                <div class="card-subtext">Active ledger records</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with a2:
        st.markdown(
            f"""
            <div class="fintech-card">
                <div class="card-label">Total Cumulative Spend</div>
                <div class="card-value">${analytics['total_spend']:,.2f}</div>
                <div class="card-subtext">Reconciled expenditure</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with a3:
        st.markdown(
            f"""
            <div class="fintech-card">
                <div class="card-label">Average Invoice Value</div>
                <div class="card-value">${analytics['avg_amount']:,.2f}</div>
                <div class="card-subtext">Per transaction mean</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with a4:
        validated_count = analytics["status_breakdown"].get("VALIDATED", 0)
        pass_rate = (validated_count / analytics["total_invoices"] * 100) if analytics["total_invoices"] > 0 else 100
        st.markdown(
            f"""
            <div class="fintech-card">
                <div class="card-label">Reconciliation Rate</div>
                <div class="card-value" style="color:#059669;">{pass_rate:.1f}%</div>
                <div class="card-subtext">Audit certified ratio</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Search & Filter Controls
    f1, f2, f3 = st.columns([2, 1, 1])
    with f1:
        search_query = st.text_input("🔍 Search Ledger by Vendor, Invoice # or PO", placeholder="e.g. Apex Hardware or INV-2026")
    with f2:
        vendor_filter = st.selectbox("Vendor Filter", ["All"] + [v["vendor_name"] for v in analytics["top_vendors"]])
    with f3:
        status_filter = st.selectbox("Audit Status", ["All", "VALIDATED", "PENDING", "DISCREPANCY"])

    db_invoices = repo.get_invoices(
        search_query=search_query,
        vendor=vendor_filter,
        status=status_filter,
    )

    if db_invoices:
        df_db = pd.DataFrame(db_invoices)
        display_cols = ["id", "vendor_name", "invoice_number", "invoice_date", "currency", "total_amount", "validation_status", "created_at"]
        st.dataframe(df_db[display_cols], use_container_width=True, hide_index=True)

        st.markdown("#### 📥 Multi-Format Audit Export Center")
        exp_col1, exp_col2, exp_col3 = st.columns(3)

        with exp_col1:
            json_payload = export_to_json(db_invoices)
            st.download_button(
                "📥 Export Full Structured JSON",
                data=json_payload,
                file_name="invoices_ledger_export.json",
                mime="application/json",
                use_container_width=True,
            )

        with exp_col2:
            summary_csv = export_summary_csv(db_invoices)
            st.download_button(
                "📊 Export Summary CSV Spreadsheet",
                data=summary_csv,
                file_name="invoices_summary_report.csv",
                mime="text/csv",
                use_container_width=True,
            )

        with exp_col3:
            detailed_list = []
            for inv in db_invoices:
                full_inv = repo.get_invoice_by_id(inv["id"])
                if full_inv:
                    detailed_list.append(full_inv)
            detailed_csv = export_detailed_items_csv(detailed_list)
            st.download_button(
                "📋 Export Detailed Line Items CSV",
                data=detailed_csv,
                file_name="invoice_line_items_detailed.csv",
                mime="text/csv",
                use_container_width=True,
            )

        st.markdown("---")
        st.markdown("#### 🗑️ Ledger Record Management")
        d1, d2 = st.columns([3, 1])
        with d1:
            del_id = st.selectbox("Select Record ID to delete", [inv["id"] for inv in db_invoices], format_func=lambda x: f"Invoice #{x}")
        with d2:
            if st.button("Permanently Delete", type="secondary"):
                if repo.delete_invoice(del_id):
                    st.success(f"Invoice record #{del_id} deleted.")
                    st.rerun()

    else:
        st.info("No matching records found in SQLite ledger.")
