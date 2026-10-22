"""INVOICE INTELLIGENCE — Document Processing & Financial Operations.

A financial document intelligence and accounts payable operations platform
featuring automated OCR extraction, arithmetic reconciliation, multi-signal duplicate
detection, vendor directories, rules-based validation, and relational ledger persistence.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from PIL import Image
import streamlit as st

import config
from src.batch.batch_manager import BatchManager
from src.database.repository import InvoiceRepository
from src.exporter.csv_exporter import export_detailed_items_csv, export_summary_csv
from src.exporter.excel_exporter import export_duplicates_to_csv, export_exceptions_to_csv, export_to_excel
from src.exporter.json_exporter import export_to_json
from src.ocr.engine import OCREngine
from src.ocr.pdf_processor import PDFProcessor
from src.parser.extractor import FieldExtractor
from src.validator.duplicate_detector import DuplicateDetector
from src.validator.rule_engine import ValidationRuleEngine
from src.validator.schema_validator import validate_invoice_payload

# Initialize Page Configuration with Sidebar Collapsed
st.set_page_config(
    page_title="Invoice Intelligence | Financial Operations",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ==============================================================================
# SESSION STATE INITIALIZATION
# ==============================================================================
def init_session_state() -> None:
    if "theme" not in st.session_state:
        st.session_state.theme = "Editorial Light"
    if "nav_section" not in st.session_state:
        st.session_state.nav_section = "Overview"
    if "active_domain" not in st.session_state:
        st.session_state.active_domain = "WORKSPACE"
    if "current_file_name" not in st.session_state:
        st.session_state.current_file_name = None
    if "ocr_result" not in st.session_state:
        st.session_state.ocr_result = None
    if "extracted_data" not in st.session_state:
        st.session_state.extracted_data = None
    if "validation_report" not in st.session_state:
        st.session_state.validation_report = None
    if "duplicate_report" not in st.session_state:
        st.session_state.duplicate_report = None
    if "pdf_page_idx" not in st.session_state:
        st.session_state.pdf_page_idx = 0
    if "pdf_pages_cache" not in st.session_state:
        st.session_state.pdf_pages_cache = []
    if "last_saved_id" not in st.session_state:
        st.session_state.last_saved_id = None
    if "selected_invoice_id" not in st.session_state:
        st.session_state.selected_invoice_id = None
    if "queue_filter" not in st.session_state:
        st.session_state.queue_filter = "ALL"


init_session_state()


@st.cache_resource
def get_ocr_engine() -> OCREngine:
    return OCREngine()


@st.cache_resource
def get_repository() -> InvoiceRepository:
    return InvoiceRepository()


@st.cache_resource
def get_batch_manager() -> BatchManager:
    return BatchManager()


engine = get_ocr_engine()
repo = get_repository()
batch_mgr = get_batch_manager()
diag = config.get_system_diagnostics()

# ==============================================================================
# DOMAIN & WORKSPACE MAPPING
# ==============================================================================
DOMAINS = {
    "WORKSPACE": ["Overview", "My Work Queue", "All Invoices", "Vendors"],
    "DOCUMENT OPERATIONS": ["Import Center", "Extraction Studio", "Validation & Exceptions", "Duplicate Review"],
    "FINANCIAL OPERATIONS": ["Reconciliation", "Financial Insights", "Reports & Exports"],
    "SYSTEM": ["Activity & Audit", "Settings"],
}

# Automatically sync active_domain with current nav_section
for d_name, w_list in DOMAINS.items():
    if st.session_state.nav_section in w_list:
        st.session_state.active_domain = d_name
        break

# ==============================================================================
# THEME & DESIGN TOKENS (EDITORIAL OPERATIONS SOFTWARE)
# ==============================================================================
is_dark = st.session_state.theme == "Editorial Dark"

if is_dark:
    BG_COLOR = "#0D1117"
    SURFACE_COLOR = "#161B22"
    CARD_BG = "#1C2128"
    TEXT_MAIN = "#F0F6FC"
    TEXT_MUTED = "#8B949E"
    BORDER_COLOR = "#30363D"
    PRIMARY_ACCENT = "#2EA043"
    ACCENT_HOVER = "#3FB950"
    ACCENT_BG = "#0D2818"
    PILL_SUCCESS_BG = "#0D2818"
    PILL_SUCCESS_TXT = "#56D364"
    PILL_WARN_BG = "#3D2400"
    PILL_WARN_TXT = "#E3B341"
    PILL_ERR_BG = "#490202"
    PILL_ERR_TXT = "#FFA198"
    NAV_ACTIVE_BG = "#21262D"
    NAV_INACTIVE_BG = "transparent"
else:
    BG_COLOR = "#F8F7F4"
    SURFACE_COLOR = "#FFFFFF"
    CARD_BG = "#FFFFFF"
    TEXT_MAIN = "#0F172A"
    TEXT_MUTED = "#57606A"
    BORDER_COLOR = "#E2DFD7"
    PRIMARY_ACCENT = "#185A37"
    ACCENT_HOVER = "#237A4B"
    ACCENT_BG = "#EDF7F1"
    PILL_SUCCESS_BG = "#EDF7F1"
    PILL_SUCCESS_TXT = "#185A37"
    PILL_WARN_BG = "#FFF8C5"
    PILL_WARN_TXT = "#9A6700"
    PILL_ERR_BG = "#FFEBE9"
    PILL_ERR_TXT = "#CF222E"
    NAV_ACTIVE_BG = "#FFFFFF"
    NAV_INACTIVE_BG = "transparent"

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    /* AGGRESSIVELY HIDE SIDEBAR & SPREAD FULL-WIDTH */
    section[data-testid="stSidebar"] {{
        display: none !important;
    }}
    [data-testid="collapsedControl"] {{
        display: none !important;
    }}
    .main .block-container {{
        max-width: 100% !important;
        padding-top: 1rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        padding-bottom: 3rem !important;
    }}

    .stApp {{
        background-color: {BG_COLOR};
        color: {TEXT_MAIN};
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }}

    /* TOP COMMAND BAR */
    .app-topbar {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.65rem 0;
        margin-bottom: 0.75rem;
        border-bottom: 1px solid {BORDER_COLOR};
    }}
    .brand-mark {{
        font-size: 1.25rem;
        font-weight: 800;
        letter-spacing: -0.025em;
        color: {TEXT_MAIN};
        display: flex;
        align-items: center;
        gap: 0.6rem;
    }}
    .brand-pill {{
        font-size: 0.68rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        background: {ACCENT_BG};
        color: {PRIMARY_ACCENT};
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        border: 1px solid {PRIMARY_ACCENT}33;
    }}
    .status-pill {{
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        background: {ACCENT_BG};
        border: 1px solid {PRIMARY_ACCENT}33;
        padding: 0.25rem 0.6rem;
        border-radius: 9999px;
    }}
    .status-dot {{
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background-color: {PRIMARY_ACCENT};
        box-shadow: 0 0 6px {PRIMARY_ACCENT}88;
        display: inline-block;
    }}
    .status-text {{
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        color: {PRIMARY_ACCENT};
    }}

    /* TOP NAVIGATION PILLS */
    div[data-testid="stPills"], div[data-testid="stButtonGroup"] {{
        background-color: {CARD_BG};
        border: 1px solid {BORDER_COLOR};
        border-radius: 8px;
        padding: 0.45rem 0.6rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02);
        margin-bottom: 0.65rem;
    }}
    div[data-testid="stPills"] button, div[data-testid="stButtonGroup"] button {{
        border-radius: 6px !important;
        font-size: 0.8rem !important;
        font-weight: 600 !important;
        padding: 0.35rem 0.75rem !important;
        transition: all 0.15s ease-in-out !important;
        border: 1px solid transparent !important;
    }}
    div[data-testid="stPills"] button:hover, div[data-testid="stButtonGroup"] button:hover {{
        border-color: {BORDER_COLOR} !important;
        background-color: {BG_COLOR} !important;
    }}

    /* NAV RIBBON */
    .nav-ribbon {{
        background: {SURFACE_COLOR};
        border: 1px solid {BORDER_COLOR};
        border-radius: 6px;
        padding: 0.4rem 0.6rem;
        margin-bottom: 1.25rem;
        display: flex;
        flex-direction: column;
        gap: 0.4rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    }}
    .domain-bar {{
        display: flex;
        align-items: center;
        gap: 0.4rem;
        border-bottom: 1px solid {BORDER_COLOR}66;
        padding-bottom: 0.35rem;
    }}
    .subnav-bar {{
        display: flex;
        align-items: center;
        gap: 0.4rem;
        flex-wrap: wrap;
    }}

    /* METRIC CARDS */
    .metric-card {{
        background-color: {CARD_BG};
        border: 1px solid {BORDER_COLOR};
        border-radius: 4px;
        padding: 1rem 1.15rem;
        box-shadow: 0 1px 2px rgba(0,0,0,0.02);
        margin-bottom: 0.75rem;
    }}
    .metric-label {{
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: {TEXT_MUTED};
        margin-bottom: 0.25rem;
    }}
    .metric-value {{
        font-size: 1.6rem;
        font-weight: 800;
        color: {TEXT_MAIN};
        font-family: 'JetBrains Mono', monospace;
        font-variant-numeric: tabular-nums;
        letter-spacing: -0.02em;
    }}
    .metric-subtext {{
        font-size: 0.74rem;
        color: {TEXT_MUTED};
        margin-top: 0.2rem;
    }}

    /* STATUS BADGES */
    .status-badge {{
        display: inline-block;
        font-size: 0.72rem;
        font-weight: 600;
        padding: 0.2rem 0.55rem;
        border-radius: 3px;
        font-family: 'JetBrains Mono', monospace;
    }}
    .status-success {{ background: {PILL_SUCCESS_BG}; color: {PILL_SUCCESS_TXT}; border: 1px solid {PILL_SUCCESS_TXT}44; }}
    .status-warning {{ background: {PILL_WARN_BG}; color: {PILL_WARN_TXT}; border: 1px solid {PILL_WARN_TXT}44; }}
    .status-error {{ background: {PILL_ERR_BG}; color: {PILL_ERR_TXT}; border: 1px solid {PILL_ERR_TXT}44; }}

    /* PIPELINE TRACKER */
    .pipeline-container {{
        display: flex;
        align-items: center;
        gap: 0.5rem;
        background: {CARD_BG};
        border: 1px solid {BORDER_COLOR};
        padding: 0.85rem 1.25rem;
        border-radius: 4px;
        margin-bottom: 1.15rem;
        overflow-x: auto;
    }}
    .pipeline-step {{
        display: flex;
        flex-direction: column;
        align-items: center;
        flex: 1;
        min-width: 90px;
    }}
    .pipeline-title {{
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: {TEXT_MUTED};
    }}
    .pipeline-count {{
        font-size: 1.3rem;
        font-weight: 800;
        font-family: 'JetBrains Mono', monospace;
        color: {PRIMARY_ACCENT};
    }}
    .pipeline-arrow {{
        color: {TEXT_MUTED};
        font-size: 0.95rem;
    }}

    .tabular-num {{
        font-family: 'JetBrains Mono', monospace;
        font-variant-numeric: tabular-nums;
    }}

    /* CUSTOM SWITCH DESIGN FOR THEME TOGGLE */
    div[data-testid="stToggle"] label p {{
        font-size: 0.8rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.02em !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ==============================================================================
# TOP BAR NAVIGATION & SWITCH-LIKE THEME TOGGLE (NO SIDEBAR)
# ==============================================================================
top_col1, top_col2 = st.columns([7, 3], gap="medium")

with top_col1:
    st.markdown(
        f"""
        <div style="display:flex; align-items:center; gap:0.75rem;">
            <div style="font-size:1.6rem; line-height:1;">🧾</div>
            <div>
                <div style="display:flex; align-items:center; gap:0.5rem;">
                    <span style="font-size:1.2rem; font-weight:800; letter-spacing:-0.03em; color:{TEXT_MAIN};">INVOICE INTELLIGENCE</span>
                    <span class="brand-pill">FINANCIAL OPERATIONS</span>
                </div>
                <div style="font-size:0.74rem; color:{TEXT_MUTED}; font-weight:500;">Automated Extraction, Duplicate Detection & Relational Ledger Control</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with top_col2:
    is_dark_active = st.session_state.theme == "Editorial Dark"
    toggle_val = st.toggle(
        "🌙 Dark Theme" if is_dark_active else "☀️ Light Theme",
        value=is_dark_active,
        key="editorial_theme_switch",
    )
    if toggle_val != is_dark_active:
        st.session_state.theme = "Editorial Dark" if toggle_val else "Editorial Light"
        st.rerun()

# Dynamic Notification Counts
try:
    active_queue_count = len(repo.get_work_queue())
    all_invoices_cache = repo.get_invoices(limit=250)
    exceptions_count = len(ValidationRuleEngine.evaluate_all(all_invoices_cache))
    duplicate_pairs_count = len(DuplicateDetector.find_all_duplicate_pairs(all_invoices_cache))
except Exception:
    active_queue_count = 0
    exceptions_count = 0
    duplicate_pairs_count = 0

# Single-Tier Intuitive Navigation Bar
NAV_SECTIONS = [
    "Overview",
    "Import Center",
    "Extraction Studio",
    "My Work Queue",
    "Validation & Exceptions",
    "Duplicate Review",
    "All Invoices",
    "Vendors",
    "Reconciliation",
    "Financial Insights",
    "Reports & Exports",
    "Activity & Audit",
    "Settings",
]

NAV_DISPLAY_META = {
    "Overview": ("📊", "Overview"),
    "Import Center": ("📥", "Import"),
    "Extraction Studio": ("🔍", "Extraction Studio"),
    "My Work Queue": ("📋", "Work Queue"),
    "Validation & Exceptions": ("⚠️", "Exceptions"),
    "Duplicate Review": ("👥", "Duplicates"),
    "All Invoices": ("📑", "Invoice Ledger"),
    "Vendors": ("🏢", "Vendors"),
    "Reconciliation": ("⚖️", "Reconciliation"),
    "Financial Insights": ("📈", "Analytics"),
    "Reports & Exports": ("📤", "Exports"),
    "Activity & Audit": ("📜", "Audit Log"),
    "Settings": ("⚙️", "Settings"),
}


def format_nav_item(item_id: str) -> str:
    icon, label = NAV_DISPLAY_META.get(item_id, ("📄", item_id))
    if item_id == "My Work Queue" and active_queue_count > 0:
        return f"{icon} {label} ({active_queue_count})"
    elif item_id == "Validation & Exceptions" and exceptions_count > 0:
        return f"{icon} {label} ({exceptions_count})"
    elif item_id == "Duplicate Review" and duplicate_pairs_count > 0:
        return f"{icon} {label} ({duplicate_pairs_count})"
    return f"{icon} {label}"


selected_nav = st.pills(
    "Navigation Menu",
    options=NAV_SECTIONS,
    default=st.session_state.nav_section if st.session_state.nav_section in NAV_SECTIONS else "Overview",
    format_func=format_nav_item,
    selection_mode="single",
    required=True,
    label_visibility="collapsed",
)

if selected_nav and selected_nav != st.session_state.nav_section:
    st.session_state.nav_section = selected_nav
    for d_name, w_list in DOMAINS.items():
        if selected_nav in w_list:
            st.session_state.active_domain = d_name
            break
    st.rerun()

BREADCRUMB_MAP = {
    "Overview": ("WORKSPACE", "Executive Overview & Operations Cockpit", "High-level metrics, processing funnel, recent invoice feed, and immediate actions."),
    "Import Center": ("DOCUMENT OPERATIONS", "Document Ingestion & Batch Processor", "Upload single invoices or batch process multi-page PDFs and images."),
    "Extraction Studio": ("DOCUMENT OPERATIONS", "OCR Extraction Studio", "Interactive inspection of extracted bounding boxes, confidence scores, and fields."),
    "My Work Queue": ("OPERATIONS", "Accounts Payable Work Queue", "Prioritized review queue for unreviewed, pending, and flagged documents."),
    "Validation & Exceptions": ("OPERATIONS", "Validation & Rule Exceptions", "Automated compliance checks, arithmetic discrepancies, and chronology alerts."),
    "Duplicate Review": ("OPERATIONS", "Duplicate Detection & Resolution", "Multi-signal duplicate analysis, confidence scoring, and side-by-side reconciliation."),
    "All Invoices": ("FINANCIAL LEDGER", "Relational Invoice Ledger", "Searchable record of all processed invoices, line items, and approval states."),
    "Vendors": ("FINANCIAL LEDGER", "Vendor Directory & Spend Analysis", "Vendor profiles, aggregate expenditures, invoice counts, and directory management."),
    "Reconciliation": ("FINANCIAL LEDGER", "Arithmetic & Tax Reconciliation", "Comprehensive verification of subtotal, tax, and shipping against document totals."),
    "Financial Insights": ("FINANCIAL OPERATIONS", "Financial Insights & Spend Analytics", "Spend distribution across vendors, status breakdown, and volume trends."),
    "Reports & Exports": ("FINANCIAL OPERATIONS", "Reports & Multi-Format Exporter", "Audit-grade exports to Excel (multi-sheet), Summary CSV, Detailed CSV, and JSON."),
    "Activity & Audit": ("SYSTEM", "Activity Log & Audit Trail", "Complete chronological ledger of approvals, modifications, and system events."),
    "Settings": ("SYSTEM", "Settings & Platform Environment", "Operational status, ledger storage controls, and demo data management."),
}

domain_tag, page_title, page_desc = BREADCRUMB_MAP.get(
    st.session_state.nav_section,
    ("WORKSPACE", st.session_state.nav_section, "Financial operations workspace."),
)

st.markdown(
    f"""
    <div style="display:flex; justify-content:space-between; align-items:center; padding:0.25rem 0 0.85rem 0; border-bottom:1px solid {BORDER_COLOR}; margin-bottom:1.15rem;">
        <div>
            <div style="font-size:0.68rem; font-weight:700; text-transform:uppercase; letter-spacing:0.07em; color:{PRIMARY_ACCENT}; margin-bottom:0.15rem;">
                {domain_tag} &nbsp;›&nbsp; {page_title}
            </div>
            <div style="font-size:0.8rem; color:{TEXT_MUTED}; font-weight:500;">
                {page_desc}
            </div>
        </div>
        <div class="status-pill">
            <span class="status-dot"></span>
            <span class="status-text">Ready</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ==============================================================================
# WORKSPACE 1: OVERVIEW (ACTIONABLE OPERATIONS DESK)
# ==============================================================================
def render_overview() -> None:
    st.markdown(
        f"""
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
            <div>
                <h3 style="margin:0; font-weight:800; letter-spacing:-0.02em;">Operations Desk</h3>
                <div style="font-size:0.8rem; color:{TEXT_MUTED};">Real-time accounts payable status and actionable exception queue</div>
            </div>
            <div class="status-badge status-success">All Ledger Services Active</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    analytics = repo.get_analytics_summary()
    currency_spend = repo.get_currency_spend_summary()
    queue_items = repo.get_work_queue()
    stage_counts = repo.get_pipeline_stage_counts()
    recent_activity = repo.get_recent_activity(limit=6)

    # Section A: Operational Summary
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Total Invoices</div>
                <div class="metric-value">{analytics['total_invoices']}</div>
                <div class="metric-subtext">Registered in ledger</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        primary_spend = f"${analytics['total_spend']:,.2f}"
        curr_label = "USD"
        if currency_spend:
            primary_spend = f"${currency_spend[0]['total_amount']:,.2f}"
            curr_label = currency_spend[0]["currency"]
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Volume ({curr_label})</div>
                <div class="metric-value">{primary_spend}</div>
                <div class="metric-subtext">{len(currency_spend)} Currencies tracked</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col3:
        high_priority = sum(1 for q in queue_items if q.get("priority") == "HIGH")
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Work Queue</div>
                <div class="metric-value" style="color: {'#CF222E' if high_priority > 0 else TEXT_MAIN};">{len(queue_items)}</div>
                <div class="metric-subtext">{high_priority} High priority issues</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col4:
        all_invoices = repo.get_invoices(limit=250)
        exceptions = ValidationRuleEngine.evaluate_all(all_invoices)
        crit_count = sum(1 for e in exceptions if e.severity == "CRITICAL")
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Exceptions</div>
                <div class="metric-value" style="color: {'#CF222E' if crit_count > 0 else TEXT_MAIN};">{len(exceptions)}</div>
                <div class="metric-subtext">{crit_count} Critical findings</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col5:
        dup_pairs = DuplicateDetector.find_all_duplicate_pairs(all_invoices)
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Duplicate Pairs</div>
                <div class="metric-value">{len(dup_pairs)}</div>
                <div class="metric-subtext">Potential double billings</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Section D: Invoice Pipeline Stages
    st.markdown(
        f"""
        <div class="pipeline-container">
            <div class="pipeline-step">
                <span class="pipeline-title">Imported</span>
                <span class="pipeline-count">{stage_counts.get('IMPORTED', 0)}</span>
            </div>
            <span class="pipeline-arrow">→</span>
            <div class="pipeline-step">
                <span class="pipeline-title">Extracted</span>
                <span class="pipeline-count">{stage_counts.get('EXTRACTED', 0)}</span>
            </div>
            <span class="pipeline-arrow">→</span>
            <div class="pipeline-step">
                <span class="pipeline-title">Under Review</span>
                <span class="pipeline-count">{stage_counts.get('UNDER_REVIEW', 0)}</span>
            </div>
            <span class="pipeline-arrow">→</span>
            <div class="pipeline-step">
                <span class="pipeline-title">Validated</span>
                <span class="pipeline-count">{stage_counts.get('VALIDATED', 0)}</span>
            </div>
            <span class="pipeline-arrow">→</span>
            <div class="pipeline-step">
                <span class="pipeline-title">Reconciled</span>
                <span class="pipeline-count">{stage_counts.get('RECONCILED', 0)}</span>
            </div>
            <span class="pipeline-arrow">→</span>
            <div class="pipeline-step">
                <span class="pipeline-title">Exported</span>
                <span class="pipeline-count">{stage_counts.get('EXPORTED', 0)}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Section B: Work Requiring Attention vs Section C: Recent Operations
    left_col, right_col = st.columns([3, 2], gap="large")

    with left_col:
        st.markdown("##### 🚨 Work Requiring Immediate Attention")
        if not queue_items:
            st.success("Clear Queue — All documents have been reviewed and validated.")
        else:
            for item in queue_items[:4]:
                with st.container():
                    st.markdown(
                        f"""
                        <div style="background:{CARD_BG}; border:1px solid {BORDER_COLOR}; border-left: 4px solid {'#CF222E' if item['priority']=='HIGH' else '#E3B341'}; padding:0.65rem 0.95rem; margin-bottom:0.4rem; border-radius:3px;">
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <span style="font-weight:700; font-size:0.88rem;">{item.get('vendor_name', 'Unknown')} · #{item.get('invoice_number', 'N/A')}</span>
                                <span class="status-badge {'status-error' if item['priority']=='HIGH' else 'status-warning'}">{item['queue_category']}</span>
                            </div>
                            <div style="font-size:0.78rem; color:{TEXT_MUTED}; margin-top:0.25rem;">{item['issue_reason']}</div>
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-top:0.35rem; font-size:0.75rem;">
                                <span class="tabular-num" style="font-weight:700;">{item.get('currency','USD')} ${float(item.get('total_amount',0.0) or 0.0):,.2f}</span>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    c_btn, _ = st.columns([1, 4])
                    with c_btn:
                        if st.button("Resolve", key=f"ov_res_{item.get('id')}", use_container_width=True):
                            st.session_state.selected_invoice_id = item.get("id")
                            st.session_state.nav_section = "Extraction Studio"
                            st.session_state.active_domain = "DOCUMENT OPERATIONS"
                            st.rerun()

    with right_col:
        st.markdown("##### ⏱️ Recent Processing Activity")
        if not recent_activity:
            st.info("No recorded activity entries found.")
        else:
            for act in recent_activity:
                st.markdown(
                    f"""
                    <div style="font-size:0.78rem; padding:0.45rem 0; border-bottom:1px solid {BORDER_COLOR};">
                        <div style="display:flex; justify-content:space-between;">
                            <span style="font-weight:600;">{act.get('action')}</span>
                            <span style="color:{TEXT_MUTED}; font-size:0.7rem;">{act.get('changed_at')}</span>
                        </div>
                        <div style="color:{TEXT_MUTED};">#{act.get('invoice_number')} ({act.get('vendor_name')}): {act.get('field_name')}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


# ==============================================================================
# WORKSPACE 2: MY WORK QUEUE
# ==============================================================================
def render_work_queue() -> None:
    st.markdown(
        f"""
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
            <div>
                <h3 style="margin:0; font-weight:800; letter-spacing:-0.02em;">My Work Queue</h3>
                <div style="font-size:0.8rem; color:{TEXT_MUTED};">Task-oriented exception inbox prioritized by operational severity</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    filter_cols = st.columns([2, 1, 1])
    with filter_cols[0]:
        cat_filter = st.selectbox(
            "Filter Category",
            ["ALL", "MISSING_INFO", "VALIDATION_FAILED", "POTENTIAL_DUPLICATE", "RECONCILIATION_REQUIRED", "NEEDS_REVIEW"],
            index=0,
            label_visibility="collapsed",
        )
    with filter_cols[1]:
        search_q = st.text_input("Search Queue", placeholder="Vendor or Invoice #...", label_visibility="collapsed")
    with filter_cols[2]:
        sort_by = st.selectbox("Sort", ["Priority (High First)", "Amount (High First)", "Date"], label_visibility="collapsed")

    items = repo.get_work_queue(category=None if cat_filter == "ALL" else cat_filter)

    if search_q:
        q_lower = search_q.strip().lower()
        items = [i for i in items if q_lower in str(i.get("vendor_name", "")).lower() or q_lower in str(i.get("invoice_number", "")).lower()]

    if sort_by == "Priority (High First)":
        items.sort(key=lambda x: (0 if x.get("priority") == "HIGH" else 1 if x.get("priority") == "MEDIUM" else 2))
    elif sort_by == "Amount (High First)":
        items.sort(key=lambda x: float(x.get("total_amount", 0.0) or 0.0), reverse=True)

    st.markdown(f"<div style='font-size:0.8rem; color:{TEXT_MUTED}; margin-bottom:0.75rem;'>Showing {len(items)} actionable tasks</div>", unsafe_allow_html=True)

    if not items:
        st.success("No outstanding issues matching this filter. Queue is clear!")
        return

    for item in items:
        p_color = "#CF222E" if item.get("priority") == "HIGH" else "#E3B341"
        with st.container():
            st.markdown(
                f"""
                <div style="background:{CARD_BG}; border:1px solid {BORDER_COLOR}; border-left: 4px solid {p_color}; padding:0.85rem 1.15rem; margin-bottom:0.6rem; border-radius:4px;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <span style="font-weight:700; font-size:0.95rem;">{item.get('vendor_name')}</span>
                            <span style="color:{TEXT_MUTED}; font-size:0.85rem; margin-left:0.5rem;">#{item.get('invoice_number')}</span>
                        </div>
                        <div style="display:flex; gap:0.5rem; align-items:center;">
                            <span class="status-badge {'status-error' if item['priority']=='HIGH' else 'status-warning'}">{item['queue_category']}</span>
                            <span class="tabular-num" style="font-weight:700; font-size:1rem;">{item.get('currency','USD')} ${float(item.get('total_amount', 0.0) or 0.0):,.2f}</span>
                        </div>
                    </div>
                    <div style="font-size:0.82rem; color:{TEXT_MAIN}; margin-top:0.35rem;">
                        <strong>Issue:</strong> {item['issue_reason']}
                    </div>
                    <div style="font-size:0.75rem; color:{TEXT_MUTED}; margin-top:0.25rem;">
                        Date: {item.get('invoice_date') or 'Missing'} · Line Items: {item.get('item_count', 0)} · File: {item.get('filename') or 'Uploaded document'}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            act_cols = st.columns([1, 1, 4])
            with act_cols[0]:
                if st.button("Open in Studio", key=f"wq_open_{item.get('id')}_{item.get('queue_category')}", use_container_width=True):
                    st.session_state.selected_invoice_id = item.get("id")
                    st.session_state.nav_section = "Extraction Studio"
                    st.session_state.active_domain = "DOCUMENT OPERATIONS"
                    st.rerun()
            with act_cols[1]:
                if st.button("Reconcile", key=f"wq_rec_{item.get('id')}_{item.get('queue_category')}", use_container_width=True):
                    st.session_state.selected_invoice_id = item.get("id")
                    st.session_state.nav_section = "Reconciliation"
                    st.session_state.active_domain = "FINANCIAL OPERATIONS"
                    st.rerun()


# ==============================================================================
# WORKSPACE 3: ALL INVOICES (PRIMARY REGISTER & LEDGER)
# ==============================================================================
def render_all_invoices() -> None:
    st.markdown(
        f"""
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
            <div>
                <h3 style="margin:0; font-weight:800; letter-spacing:-0.02em;">All Invoices</h3>
                <div style="font-size:0.8rem; color:{TEXT_MUTED};">Complete searchable relational ledger and itemized line-item catalog</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    f_col1, f_col2, f_col3, f_col4 = st.columns([3, 2, 2, 2])
    with f_col1:
        search_query = st.text_input("Search Invoices", placeholder="Search vendor, invoice #, PO...", label_visibility="collapsed")
    with f_col2:
        status_filter = st.selectbox("Status", ["All", "VALIDATED", "VERIFIED_WITH_WARNINGS", "NEEDS_REVIEW"], label_visibility="collapsed")
    with f_col3:
        currency_filter = st.selectbox("Currency", ["All", "USD", "EUR", "GBP", "CAD"], label_visibility="collapsed")
    with f_col4:
        sort_by = st.selectbox("Sort", ["created_at", "total_amount", "vendor_name", "invoice_date"], label_visibility="collapsed")

    invoices = repo.get_invoices(
        search_query=search_query,
        status=status_filter if status_filter != "All" else None,
        currency=currency_filter if currency_filter != "All" else None,
        sort_by=sort_by,
        sort_order="DESC",
        limit=250,
    )

    if not invoices:
        st.info("No invoice records found matching your filters.")
        return

    st.markdown(f"<div style='font-size:0.8rem; color:{TEXT_MUTED}; margin-bottom:0.5rem;'>Displaying {len(invoices)} invoices</div>", unsafe_allow_html=True)

    table_rows = []
    for inv in invoices:
        table_rows.append({
            "ID": inv.get("id"),
            "Vendor": inv.get("vendor_name"),
            "Invoice #": inv.get("invoice_number"),
            "Date": inv.get("invoice_date") or "-",
            "Total": f"{inv.get('currency', 'USD')} ${float(inv.get('total_amount', 0.0) or 0.0):,.2f}",
            "Status": inv.get("validation_status"),
            "Pipeline": inv.get("processing_status", "EXTRACTED"),
            "Duplicate": "Flagged" if inv.get("is_duplicate") == 1 else "Clear",
        })

    df = pd.DataFrame(table_rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Detailed Record Drawer
    st.markdown("---")
    st.markdown("##### 🔍 Inspect Invoice Record")
    inv_ids = [inv.get("id") for inv in invoices]
    selected_id = st.selectbox("Select Invoice ID to inspect", inv_ids, index=0)

    if selected_id:
        record = repo.get_invoice_by_id(selected_id)
        if record:
            meta_cols = st.columns(4)
            with meta_cols[0]:
                st.caption("Vendor Name")
                st.write(record.get("vendor_name"))
            with meta_cols[1]:
                st.caption("Invoice Number")
                st.write(record.get("invoice_number"))
            with meta_cols[2]:
                st.caption("Total Payable")
                st.write(f"**{record.get('currency')} ${float(record.get('total_amount',0.0) or 0.0):,.2f}**")
            with meta_cols[3]:
                st.caption("Validation Status")
                st.write(record.get("validation_status"))

            items = record.get("line_items", [])
            if items:
                st.markdown("###### Itemized Line Items")
                items_df = pd.DataFrame(items)[["description", "quantity", "unit_price", "amount"]]
                items_df.columns = ["Description", "Quantity", "Unit Price", "Total Amount"]
                st.dataframe(items_df, use_container_width=True, hide_index=True)

            trail = record.get("audit_trail", [])
            if trail:
                with st.expander(f"Audit Trail ({len(trail)} entries)"):
                    for tr in trail:
                        st.caption(f"**{tr.get('action')}** · {tr.get('changed_at')} · Field: `{tr.get('field_name')}`: `{tr.get('old_value')}` → `{tr.get('new_value')}`")

            btn_cols = st.columns([1, 1, 1, 3])
            with btn_cols[0]:
                if st.button("Open in Studio", key=f"inv_open_{selected_id}"):
                    st.session_state.selected_invoice_id = selected_id
                    st.session_state.nav_section = "Extraction Studio"
                    st.session_state.active_domain = "DOCUMENT OPERATIONS"
                    st.rerun()
            with btn_cols[1]:
                if st.button("Reconcile", key=f"inv_rec_{selected_id}"):
                    st.session_state.selected_invoice_id = selected_id
                    st.session_state.nav_section = "Reconciliation"
                    st.session_state.active_domain = "FINANCIAL OPERATIONS"
                    st.rerun()
            with btn_cols[2]:
                if st.button("Delete Record", key=f"inv_del_{selected_id}", type="secondary"):
                    repo.delete_invoice(selected_id)
                    st.success(f"Invoice #{selected_id} deleted.")
                    st.rerun()


# ==============================================================================
# WORKSPACE 4: VENDORS (DIRECTORY & GOVERNANCE)
# ==============================================================================
def render_vendors() -> None:
    st.markdown(
        f"""
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
            <div>
                <h3 style="margin:0; font-weight:800; letter-spacing:-0.02em;">Vendors Directory</h3>
                <div style="font-size:0.8rem; color:{TEXT_MUTED};">Counterparty governance, currency-segregated spend, and legal name normalization</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    search_v = st.text_input("Search Vendors", placeholder="Enter vendor name to search...", label_visibility="collapsed")
    vendors = repo.get_vendors_directory(search=search_v)

    if not vendors:
        st.info("No vendors registered in database yet.")
        return

    st.markdown(f"<div style='font-size:0.8rem; color:{TEXT_MUTED}; margin-bottom:0.75rem;'>Tracking {len(vendors)} unique vendors</div>", unsafe_allow_html=True)

    v_rows = []
    for v in vendors:
        curr_str = ", ".join(f"{c} ${amt:,.2f}" for c, amt in v["currencies"].items())
        v_rows.append({
            "Vendor Name": v["vendor_name"],
            "Total Invoices": v["total_invoices"],
            "Cumulative Spend": curr_str,
            "First Invoice": v["first_date"] or "-",
            "Latest Invoice": v["latest_date"] or "-",
        })

    st.dataframe(pd.DataFrame(v_rows), use_container_width=True, hide_index=True)

    # Safe Vendor Rename Tool
    st.markdown("---")
    st.markdown("##### ✏️ Vendor Governance & Normalization")
    st.caption("Correct misspelled vendor identities across all associated historical invoices with immutable audit logging.")

    rn_col1, rn_col2, rn_col3 = st.columns([3, 3, 2])
    with rn_col1:
        all_vendor_names = [v["vendor_name"] for v in vendors]
        old_vendor = st.selectbox("Select Existing Vendor to Rename", all_vendor_names)
    with rn_col2:
        new_vendor = st.text_input("Enter Corrected Legal Vendor Name", placeholder="e.g. Apex Hardware Labs LLC")
    with rn_col3:
        st.write("")
        st.write("")
        if st.button("Apply Rename", use_container_width=True):
            if new_vendor and new_vendor.strip() != old_vendor:
                updated = repo.rename_vendor(old_vendor, new_vendor.strip(), changed_by="Finance Operator")
                st.success(f"Renamed '{old_vendor}' to '{new_vendor}' across {updated} invoices.")
                st.rerun()
            else:
                st.warning("Please specify a distinct valid new vendor name.")


# ==============================================================================
# WORKSPACE 5: IMPORT CENTER (MULTI-FILE INGESTION & BATCH QUEUE)
# ==============================================================================
def render_import_center() -> None:
    st.markdown(
        f"""
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
            <div>
                <h3 style="margin:0; font-weight:800; letter-spacing:-0.02em;">Import Center</h3>
                <div style="font-size:0.8rem; color:{TEXT_MUTED};">Multi-file document ingestion with independent failure isolation</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_upload, tab_samples = st.tabs(["📁 Multi-Document Ingestion", "⚡ Load Synthetic Demo Invoices"])

    with tab_upload:
        uploaded_files = st.file_uploader(
            "Upload Invoices (PDF, PNG, JPG, TIFF)",
            type=["png", "jpg", "jpeg", "tiff", "pdf"],
            accept_multiple_files=True,
            help="Select one or multiple invoice documents. Each file is processed in complete isolation.",
        )

        if uploaded_files:
            st.markdown(f"**Queue:** {len(uploaded_files)} files selected")
            queue_preview = []
            for f in uploaded_files:
                size_kb = len(f.getvalue()) / 1024
                queue_preview.append({"Filename": f.name, "Size": f"{size_kb:.1f} KB", "Status": "Queued"})
            st.dataframe(pd.DataFrame(queue_preview), use_container_width=True, hide_index=True)

            if st.button("🚀 Process Ingestion Batch", type="primary", use_container_width=True):
                progress_bar = st.progress(0.0)
                status_text = st.empty()

                file_payload = [{"name": f.name, "content": f.getvalue()} for f in uploaded_files]
                total = len(file_payload)

                def update_progress(current: int, tot: int, name: str) -> None:
                    pct = current / tot
                    progress_bar.progress(pct)
                    status_text.text(f"Processing ({current}/{tot}): {name}...")

                batch_result = batch_mgr.process_batch(file_payload, progress_callback=update_progress)
                progress_bar.progress(1.0)
                status_text.empty()

                st.success(f"Batch {batch_result['batch_id']} completed: {batch_result['success_count']} succeeded, {batch_result['failed_count']} failed.")

                res_rows = []
                for res in batch_result.get("items", batch_result.get("results", [])):
                    res_rows.append({
                        "File": res.get("filename"),
                        "Status": res.get("status", "SUCCESS"),
                        "Vendor": res.get("vendor_name", "-"),
                        "Invoice #": res.get("invoice_number", "-"),
                        "Total": f"${float(res.get('total_amount', 0.0) or 0.0):,.2f}",
                        "Record ID": res.get("invoice_id") or "-",
                        "Error": res.get("error") or "-",
                    })
                st.dataframe(pd.DataFrame(res_rows), use_container_width=True, hide_index=True)

            if len(uploaded_files) == 1:
                if st.button("⚡ Open Directly in Extraction Studio", use_container_width=True):
                    f = uploaded_files[0]
                    file_bytes = f.getvalue()
                    with st.spinner("Processing OCR extraction..."):
                        if f.name.lower().endswith(".pdf"):
                            pdf_pages = PDFProcessor.extract_pages_as_images(file_bytes)
                            st.session_state.pdf_pages_cache = pdf_pages
                            st.session_state.pdf_page_idx = 0
                        else:
                            st.session_state.pdf_pages_cache = []

                        ocr_res = engine.process_document(file_bytes)
                        ext_res = FieldExtractor.extract_all(ocr_res.get("raw_text", ""))
                        ext_res["raw_text"] = ocr_res.get("raw_text", "")
                        ext_res["filename"] = f.name
                        ext_res["overall_confidence"] = ocr_res.get("mean_confidence", 0.0)

                        st.session_state.current_file_name = f.name
                        st.session_state.ocr_result = ocr_res
                        st.session_state.extracted_data = ext_res
                        st.session_state.selected_invoice_id = None
                        st.session_state.nav_section = "Extraction Studio"
                        st.rerun()

    with tab_samples:
        st.markdown("##### Synthetic Sample Invoices")
        st.caption("Curated, 100% synthetic invoice documents designed for testing clean extractions, complex line items, and edge cases.")

        sample_dir = Path("data/sample_invoices")
        sample_files = list(sample_dir.glob("*.png")) + list(sample_dir.glob("*.pdf")) if sample_dir.exists() else []

        if sample_files:
            sample_names = [f.name for f in sample_files]
            selected_sample_name = st.selectbox("Choose a sample invoice", sample_names)
            target_path = sample_dir / selected_sample_name

            if st.button("⚡ Ingest & Open in Extraction Studio", use_container_width=True):
                with open(target_path, "rb") as sf:
                    file_bytes = sf.read()

                with st.spinner("Processing OCR extraction..."):
                    if selected_sample_name.lower().endswith(".pdf"):
                        pdf_pages = PDFProcessor.extract_pages_as_images(file_bytes)
                        st.session_state.pdf_pages_cache = pdf_pages
                        st.session_state.pdf_page_idx = 0
                    else:
                        st.session_state.pdf_pages_cache = []

                    ocr_res = engine.process_document(file_bytes)
                    ext_res = FieldExtractor.extract_all(ocr_res.get("raw_text", ""))
                    ext_res["raw_text"] = ocr_res.get("raw_text", "")
                    ext_res["filename"] = selected_sample_name
                    ext_res["overall_confidence"] = ocr_res.get("mean_confidence", 0.0)

                    st.session_state.current_file_name = selected_sample_name
                    st.session_state.ocr_result = ocr_res
                    st.session_state.extracted_data = ext_res
                    st.session_state.selected_invoice_id = None
                    st.session_state.nav_section = "Extraction Studio"
                    st.session_state.active_domain = "DOCUMENT OPERATIONS"
                    st.rerun()


# ==============================================================================
# WORKSPACE 6: EXTRACTION STUDIO (SPLIT-SCREEN REVIEW WORKSTATION)
# ==============================================================================
def render_extraction_studio() -> None:
    st.markdown(
        f"""
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
            <div>
                <h3 style="margin:0; font-weight:800; letter-spacing:-0.02em;">Extraction Studio</h3>
                <div style="font-size:0.8rem; color:{TEXT_MUTED};">Full-width split-screen review workstation with live accounting formula verification</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.session_state.selected_invoice_id:
        db_inv = repo.get_invoice_by_id(st.session_state.selected_invoice_id)
        if db_inv:
            st.session_state.extracted_data = db_inv
            st.session_state.current_file_name = db_inv.get("filename") or f"Record #{db_inv.get('id')}"

    ext_data = st.session_state.extracted_data
    if not ext_data:
        st.info("No active document loaded in Extraction Studio. Ingest a document in the Import Center or pick an invoice from All Invoices.")
        if st.button("Go to Import Center"):
            st.session_state.nav_section = "Import Center"
            st.session_state.active_domain = "DOCUMENT OPERATIONS"
            st.rerun()
        return

    left_pane, right_pane = st.columns([1, 1], gap="large")

    # ==========================
    # LEFT PANE: DOCUMENT VIEWER
    # ==========================
    with left_pane:
        st.markdown(f"##### 📄 Document Preview: `{st.session_state.current_file_name or 'Document'}`")

        # Multi-page PDF controls
        if st.session_state.pdf_pages_cache and len(st.session_state.pdf_pages_cache) > 1:
            p_cols = st.columns([1, 2, 1])
            with p_cols[0]:
                if st.button("◀ Prev", disabled=st.session_state.pdf_page_idx <= 0):
                    st.session_state.pdf_page_idx -= 1
                    st.rerun()
            with p_cols[1]:
                st.caption(f"Page {st.session_state.pdf_page_idx + 1} of {len(st.session_state.pdf_pages_cache)}")
            with p_cols[2]:
                if st.button("Next ▶", disabled=st.session_state.pdf_page_idx >= len(st.session_state.pdf_pages_cache) - 1):
                    st.session_state.pdf_page_idx += 1
                    st.rerun()

        # Zoom control
        zoom_pct = st.slider("Document Zoom (%)", min_value=50, max_value=250, value=100, step=10)

        # Inspection views
        view_mode = st.radio(
            "Inspection Layer",
            ["Original Document", "Preprocessed Binary", "OCR Bounding Boxes", "Recognized Plain Text"],
            horizontal=True,
            label_visibility="collapsed",
        )

        ocr_res = st.session_state.ocr_result
        if view_mode == "Recognized Plain Text":
            raw_t = ocr_res.get("text", "") if ocr_res else ext_data.get("raw_text", "No raw OCR text available.")
            st.text_area("OCR Plain Text", value=raw_t, height=450)
        else:
            img_to_show = None
            if st.session_state.pdf_pages_cache:
                img_to_show = st.session_state.pdf_pages_cache[st.session_state.pdf_page_idx]
            elif ocr_res and "preprocessed_image" in ocr_res:
                if view_mode == "Preprocessed Binary":
                    img_to_show = ocr_res["preprocessed_image"]
                elif view_mode == "OCR Bounding Boxes" and "annotated_image" in ocr_res:
                    img_to_show = ocr_res["annotated_image"]

            if img_to_show is None:
                sample_p = Path("data/sample_invoices") / str(st.session_state.current_file_name or "")
                if sample_p.exists() and sample_p.suffix.lower() == ".png":
                    img_to_show = Image.open(sample_p)

            if img_to_show:
                w, h = img_to_show.size
                scaled_w = int(w * (zoom_pct / 100.0))
                st.image(img_to_show, width=scaled_w)
            else:
                st.info("Visual preview unavailable for this database record. Inspect OCR plain text above.")

    # ================================
    # RIGHT PANE: STRUCTURED DATA WORK
    # ================================
    with right_pane:
        st.markdown("##### ⚙️ Structured Financial Editor")

        sub_val = float(ext_data.get("subtotal", 0.0) or 0.0)
        tax_val = float(ext_data.get("tax_amount", 0.0) or 0.0)
        shp_val = float(ext_data.get("shipping_amount", 0.0) or 0.0)
        dsc_val = float(ext_data.get("discount_amount", 0.0) or 0.0)
        tot_val = float(ext_data.get("total_amount", 0.0) or 0.0)

        calc_tot = round(sub_val + tax_val + shp_val - dsc_val, 2)
        diff = round(tot_val - calc_tot, 2)
        is_balanced = abs(diff) <= 0.05 and tot_val > 0

        st.markdown(
            f"""
            <div style="background:{CARD_BG}; border:1px solid {BORDER_COLOR}; border-left: 4px solid {'#2EA043' if is_balanced else '#CF222E'}; padding:0.65rem 0.95rem; margin-bottom:0.75rem; border-radius:3px;">
                <div style="font-size:0.72rem; font-weight:700; color:{TEXT_MUTED}; text-transform:uppercase;">Accounting Balance Formula Check</div>
                <div class="tabular-num" style="font-size:0.95rem; font-weight:700; margin-top:0.2rem;">
                    Subtotal (${sub_val:,.2f}) + Tax (${tax_val:,.2f}) + Shipping (${shp_val:,.2f}) - Discount (${dsc_val:,.2f}) = ${calc_tot:,.2f}
                </div>
                <div style="font-size:0.8rem; margin-top:0.25rem; color:{'#2EA043' if is_balanced else '#CF222E'};">
                    Stated Total: ${tot_val:,.2f} · Discrepancy: ${diff:+,.2f} · {'✅ Equation Balanced' if is_balanced else '⚠️ Imbalance Flagged'}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        dup_chk = DuplicateDetector.check_duplicate(
            ext_data,
            repo.get_invoices(limit=200),
            current_id=st.session_state.selected_invoice_id,
        )
        if dup_chk.get("is_duplicate"):
            st.error(f"⚠️ Potential Duplicate Detected ({dup_chk.get('severity')}): {'; '.join(dup_chk.get('reasons', []))}")

        with st.form("invoice_editor_form"):
            r1_1, r1_2 = st.columns(2)
            with r1_1:
                e_vendor = st.text_input("Vendor Name", value=ext_data.get("vendor_name", "Unknown Vendor"))
            with r1_2:
                e_inv_no = st.text_input("Invoice Number", value=ext_data.get("invoice_number", "N/A"))

            r2_1, r2_2, r2_3 = st.columns(3)
            with r2_1:
                e_date = st.text_input("Invoice Date", value=ext_data.get("invoice_date") or "")
            with r2_2:
                e_due_date = st.text_input("Due Date", value=ext_data.get("due_date") or "")
            with r2_3:
                e_curr = st.text_input("Currency", value=ext_data.get("currency", "USD"))

            r3_1, r3_2, r3_3 = st.columns(3)
            with r3_1:
                e_po = st.text_input("PO Number", value=ext_data.get("po_number") or "")
            with r3_2:
                e_terms = st.text_input("Payment Terms", value=ext_data.get("payment_terms") or "Net 30")
            with r3_3:
                e_status = st.selectbox("Validation Status", ["VALIDATED", "VERIFIED_WITH_WARNINGS", "NEEDS_REVIEW"], index=0 if is_balanced else 2)

            st.markdown("###### Financial Totals Breakdown")
            f1, f2, f3 = st.columns(3)
            with f1:
                e_subtotal = st.number_input("Subtotal", value=sub_val, step=10.0, format="%.2f")
            with f2:
                e_tax = st.number_input("Tax Amount", value=tax_val, step=1.0, format="%.2f")
            with f3:
                e_shipping = st.number_input("Shipping", value=shp_val, step=1.0, format="%.2f")

            f4, f5, f6 = st.columns(3)
            with f4:
                e_discount = st.number_input("Discount", value=dsc_val, step=1.0, format="%.2f")
            with f5:
                e_total = st.number_input("Total Amount Due", value=tot_val, step=10.0, format="%.2f")
            with f6:
                e_paid = st.number_input("Amount Paid", value=float(ext_data.get("amount_paid", 0.0) or 0.0), step=10.0, format="%.2f")

            # Editable Line Items Data Grid
            st.markdown("###### Itemized Line Items")
            raw_items = ext_data.get("line_items", [])
            items_df_data = []
            for itm in raw_items:
                items_df_data.append({
                    "description": itm.get("description", "Item"),
                    "quantity": float(itm.get("quantity", 1.0) or 1.0),
                    "unit_price": float(itm.get("unit_price", 0.0) or 0.0),
                    "amount": float(itm.get("amount", 0.0) or 0.0),
                })
            if not items_df_data:
                items_df_data = [{"description": "General Service/Goods", "quantity": 1.0, "unit_price": tot_val, "amount": tot_val}]

            edited_df = st.data_editor(
                pd.DataFrame(items_df_data),
                num_rows="dynamic",
                use_container_width=True,
                column_config={
                    "description": st.column_config.TextColumn("Description", required=True),
                    "quantity": st.column_config.NumberColumn("Qty", min_value=0.0, step=1.0, format="%.1f"),
                    "unit_price": st.column_config.NumberColumn("Unit Price ($)", min_value=0.0, format="$%.2f"),
                    "amount": st.column_config.NumberColumn("Line Total ($)", min_value=0.0, format="$%.2f"),
                },
            )

            commit_btn = st.form_submit_button("💾 Commit Record to Ledger", type="primary", use_container_width=True)

        if commit_btn:
            line_items_payload = edited_df.to_dict("records")
            save_payload = {
                "vendor_name": e_vendor.strip(),
                "invoice_number": e_inv_no.strip(),
                "invoice_date": e_date.strip() if e_date else None,
                "due_date": e_due_date.strip() if e_due_date else None,
                "currency": e_curr.strip().upper(),
                "po_number": e_po.strip() if e_po else None,
                "payment_terms": e_terms.strip() if e_terms else None,
                "subtotal": float(e_subtotal),
                "tax_amount": float(e_tax),
                "shipping_amount": float(e_shipping),
                "discount_amount": float(e_discount),
                "total_amount": float(e_total),
                "amount_paid": float(e_paid),
                "balance_due": max(0.0, float(e_total) - float(e_paid)),
                "validation_status": e_status,
                "processing_status": "VALIDATED",
                "is_duplicate": 1 if dup_chk.get("is_duplicate") else 0,
                "line_items": line_items_payload,
            }

            if st.session_state.selected_invoice_id:
                repo.update_invoice(st.session_state.selected_invoice_id, save_payload, items=line_items_payload, action_note="STUDIO_EDIT")
                st.success(f"Invoice #{st.session_state.selected_invoice_id} successfully updated with audit trail.")
            else:
                new_id = repo.save_invoice(save_payload, items=line_items_payload, filename=st.session_state.current_file_name)
                st.session_state.selected_invoice_id = new_id
                st.success(f"Invoice successfully persisted to ledger as Record #{new_id}.")
            st.rerun()


# ==============================================================================
# WORKSPACE 7: VALIDATION & EXCEPTIONS
# ==============================================================================
def render_validation_center() -> None:
    st.markdown(
        f"""
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
            <div>
                <h3 style="margin:0; font-weight:800; letter-spacing:-0.02em;">Validation & Exceptions</h3>
                <div style="font-size:0.8rem; color:{TEXT_MUTED};">Rules-based audit station analyzing math imbalances, inverted dates, and data gaps</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    all_invoices = repo.get_invoices(limit=250)
    findings = ValidationRuleEngine.evaluate_all(all_invoices)

    crit_count = sum(1 for f in findings if f.severity == "CRITICAL")
    warn_count = sum(1 for f in findings if f.severity == "WARNING")
    info_count = sum(1 for f in findings if f.severity == "INFO")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"<div class='metric-card'><div class='metric-label'>Total Exceptions</div><div class='metric-value'>{len(findings)}</div></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='metric-card'><div class='metric-label'>Critical Findings</div><div class='metric-value' style='color:#CF222E;'>{crit_count}</div></div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='metric-card'><div class='metric-label'>Warnings</div><div class='metric-value' style='color:#E3B341;'>{warn_count}</div></div>", unsafe_allow_html=True)
    with c4:
        st.markdown(f"<div class='metric-card'><div class='metric-label'>Info Notices</div><div class='metric-value'>{info_count}</div></div>", unsafe_allow_html=True)

    sev_filter = st.radio("Filter Severity", ["ALL", "CRITICAL", "WARNING", "INFO"], horizontal=True)
    if sev_filter != "ALL":
        findings = [f for f in findings if f.severity == sev_filter]

    st.markdown(f"<div style='font-size:0.8rem; color:{TEXT_MUTED}; margin-bottom:0.75rem;'>Found {len(findings)} validation issues</div>", unsafe_allow_html=True)

    if not findings:
        st.success("No active validation exceptions found for this severity. Ledger is healthy!")
        return

    for f in findings:
        sev_color = "#CF222E" if f.severity == "CRITICAL" else "#E3B341" if f.severity == "WARNING" else "#0969DA"
        with st.container():
            st.markdown(
                f"""
                <div style="background:{CARD_BG}; border:1px solid {BORDER_COLOR}; border-left:4px solid {sev_color}; padding:0.85rem 1.15rem; margin-bottom:0.55rem; border-radius:4px;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <span class="status-badge {'status-error' if f.severity=='CRITICAL' else 'status-warning'}">{f.severity}</span>
                            <span style="font-weight:700; font-size:0.9rem; margin-left:0.5rem;">{f.rule_id}</span>
                            <span style="color:{TEXT_MUTED}; font-size:0.82rem;">· Field: <code>{f.field}</code></span>
                        </div>
                        <span style="font-weight:600; font-size:0.85rem;">{f.invoice_ref}</span>
                    </div>
                    <div style="font-size:0.82rem; margin-top:0.35rem; color:{TEXT_MAIN};">
                        <strong>Explanation:</strong> {f.explanation}
                    </div>
                    <div style="font-size:0.78rem; margin-top:0.25rem; color:{PRIMARY_ACCENT};">
                        <strong>Suggested Action:</strong> {f.suggested_action}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if f.invoice_id:
                col_btn, _ = st.columns([1, 5])
                with col_btn:
                    if st.button("Fix in Studio", key=f"ex_fix_{f.invoice_id}_{f.rule_id}"):
                        st.session_state.selected_invoice_id = f.invoice_id
                        st.session_state.nav_section = "Extraction Studio"
                        st.session_state.active_domain = "DOCUMENT OPERATIONS"
                        st.rerun()


# ==============================================================================
# WORKSPACE 8: DUPLICATE REVIEW
# ==============================================================================
def render_duplicate_review() -> None:
    st.markdown(
        f"""
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
            <div>
                <h3 style="margin:0; font-weight:800; letter-spacing:-0.02em;">Duplicate Review</h3>
                <div style="font-size:0.8rem; color:{TEXT_MUTED};">Side-by-side comparison of candidate duplicate invoices to prevent double-payments</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    all_invoices = repo.get_invoices(limit=250)
    pairs = DuplicateDetector.find_all_duplicate_pairs(all_invoices)

    st.markdown(f"<div style='font-size:0.8rem; color:{TEXT_MUTED}; margin-bottom:0.75rem;'>Detected {len(pairs)} candidate duplicate pairs</div>", unsafe_allow_html=True)

    if not pairs:
        st.success("No duplicate billing candidates detected across registered invoices.")
        return

    for idx, p in enumerate(pairs):
        a = p["invoice_a"]
        b = p["invoice_b"]
        m_type = p["match_type"]

        with st.container():
            st.markdown(
                f"""
                <div style="background:{CARD_BG}; border:1px solid {BORDER_COLOR}; border-left:4px solid {'#CF222E' if m_type=='EXACT' else '#E3B341'}; padding:1rem 1.25rem; margin-bottom:0.85rem; border-radius:4px;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">
                        <span class="status-badge {'status-error' if m_type=='EXACT' else 'status-warning'}">{m_type} DUPLICATE CANDIDATE</span>
                        <span style="font-size:0.8rem; color:{TEXT_MUTED};">Decision: <strong>{p.get('decision')}</strong></span>
                    </div>
                    <div style="font-size:0.85rem; margin-bottom:0.75rem;">{p['explanation']}</div>
                    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:1rem; background:{BG_COLOR}; padding:0.75rem; border-radius:3px;">
                        <div>
                            <div style="font-weight:700; font-size:0.85rem;">Invoice A (ID #{a.get('id')})</div>
                            <div style="font-size:0.8rem; color:{TEXT_MUTED};">Vendor: {a.get('vendor_name')}</div>
                            <div style="font-size:0.8rem; color:{TEXT_MUTED};">Number: #{a.get('invoice_number')}</div>
                            <div style="font-size:0.8rem; color:{TEXT_MUTED};">Date: {a.get('invoice_date')}</div>
                            <div class="tabular-num" style="font-weight:700; font-size:0.85rem;">Total: {a.get('currency')} ${float(a.get('total_amount',0.0) or 0.0):,.2f}</div>
                        </div>
                        <div>
                            <div style="font-weight:700; font-size:0.85rem;">Invoice B (ID #{b.get('id')})</div>
                            <div style="font-size:0.8rem; color:{TEXT_MUTED};">Vendor: {b.get('vendor_name')}</div>
                            <div style="font-size:0.8rem; color:{TEXT_MUTED};">Number: #{b.get('invoice_number')}</div>
                            <div style="font-size:0.8rem; color:{TEXT_MUTED};">Date: {b.get('invoice_date')}</div>
                            <div class="tabular-num" style="font-weight:700; font-size:0.85rem;">Total: {b.get('currency')} ${float(b.get('total_amount',0.0) or 0.0):,.2f}</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            b_cols = st.columns([2, 2, 4])
            with b_cols[0]:
                if st.button("Confirm Duplicate", key=f"dup_conf_{idx}", type="primary", use_container_width=True):
                    repo.update_duplicate_decision(b.get("id"), "CONFIRMED_DUPLICATE", notes=f"Duplicate of Record #{a.get('id')}")
                    st.success(f"Record #{b.get('id')} marked as CONFIRMED DUPLICATE.")
                    st.rerun()
            with b_cols[1]:
                if st.button("Mark Legitimate Separate", key=f"dup_leg_{idx}", use_container_width=True):
                    repo.update_duplicate_decision(b.get("id"), "LEGITIMATE_SEPARATE", notes="Verified distinct billing event")
                    st.success(f"Record #{b.get('id')} confirmed as LEGITIMATE SEPARATE.")
                    st.rerun()


# ==============================================================================
# WORKSPACE 9: RECONCILIATION
# ==============================================================================
def render_reconciliation() -> None:
    st.markdown(
        f"""
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
            <div>
                <h3 style="margin:0; font-weight:800; letter-spacing:-0.02em;">Reconciliation Workspace</h3>
                <div style="font-size:0.8rem; color:{TEXT_MUTED};">Financial consistency validation, row arithmetic cross-checks, and sign-offs</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    invoices = repo.get_invoices(limit=250)

    reconcile_rows = []
    for inv in invoices:
        sub = float(inv.get("subtotal", 0.0) or 0.0)
        tax = float(inv.get("tax_amount", 0.0) or 0.0)
        shp = float(inv.get("shipping_amount", 0.0) or 0.0)
        dsc = float(inv.get("discount_amount", 0.0) or 0.0)
        tot = float(inv.get("total_amount", 0.0) or 0.0)

        calc_tot = round(sub + tax + shp - dsc, 2)
        diff = round(tot - calc_tot, 2)
        is_balanced = abs(diff) <= 0.05 and tot > 0

        reconcile_rows.append({
            "id": inv.get("id"),
            "vendor": inv.get("vendor_name"),
            "number": inv.get("invoice_number"),
            "currency": inv.get("currency", "USD"),
            "subtotal": sub,
            "tax": tax,
            "shipping": shp,
            "discount": dsc,
            "stated_total": tot,
            "calc_total": calc_tot,
            "discrepancy": diff,
            "status": "BALANCED" if is_balanced else "DISCREPANCY",
            "rec_status": inv.get("reconciliation_status", "UNRECONCILED"),
        })

    rec_filter = st.radio("Filter", ["ALL", "DISCREPANCIES ONLY", "RECONCILED"], horizontal=True)
    if rec_filter == "DISCREPANCIES ONLY":
        reconcile_rows = [r for r in reconcile_rows if r["status"] == "DISCREPANCY"]
    elif rec_filter == "RECONCILED":
        reconcile_rows = [r for r in reconcile_rows if r["rec_status"] == "RECONCILED"]

    st.markdown(f"<div style='font-size:0.8rem; color:{TEXT_MUTED}; margin-bottom:0.75rem;'>Showing {len(reconcile_rows)} invoices for financial reconciliation</div>", unsafe_allow_html=True)

    for r in reconcile_rows:
        with st.container():
            st.markdown(
                f"""
                <div style="background:{CARD_BG}; border:1px solid {BORDER_COLOR}; border-left:4px solid {'#2EA043' if r['status']=='BALANCED' else '#CF222E'}; padding:0.85rem 1.15rem; margin-bottom:0.55rem; border-radius:4px;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <span style="font-weight:700; font-size:0.95rem;">{r['vendor']} · #{r['number']}</span>
                            <span class="status-badge {'status-success' if r['status']=='BALANCED' else 'status-error'}" style="margin-left:0.5rem;">{r['status']}</span>
                        </div>
                        <div class="tabular-num" style="font-weight:700;">{r['currency']} Stated: ${r['stated_total']:,.2f} · Calculated: ${r['calc_total']:,.2f}</div>
                    </div>
                    <div style="font-size:0.8rem; color:{TEXT_MUTED}; margin-top:0.35rem;">
                        Formula: Subtotal (${r['subtotal']:,.2f}) + Tax (${r['tax']:,.2f}) + Shipping (${r['shipping']:,.2f}) - Discount (${r['discount']:,.2f}) · Discrepancy: ${r['discrepancy']:+,.2f}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            act_cols = st.columns([1, 1, 4])
            with act_cols[0]:
                if st.button("Mark Reconciled", key=f"rec_ok_{r['id']}"):
                    repo.update_reconciliation_status(r["id"], "RECONCILED", notes="Reconciliation verified by operator")
                    st.success(f"Invoice #{r['id']} marked as RECONCILED.")
                    st.rerun()
            with act_cols[1]:
                if st.button("Adjust in Studio", key=f"rec_adj_{r['id']}"):
                    st.session_state.selected_invoice_id = r["id"]
                    st.session_state.nav_section = "Extraction Studio"
                    st.session_state.active_domain = "DOCUMENT OPERATIONS"
                    st.rerun()


# ==============================================================================
# WORKSPACE 10: FINANCIAL INSIGHTS
# ==============================================================================
def render_financial_insights() -> None:
    st.markdown(
        f"""
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
            <div>
                <h3 style="margin:0; font-weight:800; letter-spacing:-0.02em;">Financial Insights</h3>
                <div style="font-size:0.8rem; color:{TEXT_MUTED};">Database-grounded financial intelligence strictly partitioned by currency denomination</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    curr_spend = repo.get_currency_spend_summary()
    analytics = repo.get_analytics_summary()

    st.markdown("##### 💵 Spend Segregated by Currency")
    st.caption("Financial figures strictly partitioned by denomination (no cross-currency mixing).")

    if curr_spend:
        c_cols = st.columns(len(curr_spend))
        for idx, cs in enumerate(curr_spend):
            with c_cols[idx]:
                st.markdown(
                    f"""
                    <div class="metric-card">
                        <div class="metric-label">{cs['currency']} Portfolio</div>
                        <div class="metric-value">{cs['currency']} ${cs['total_amount']:,.2f}</div>
                        <div class="metric-subtext">{cs['invoice_count']} Invoices · Avg ${cs['avg_amount']:,.2f}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    c_left, c_right = st.columns(2, gap="large")
    with c_left:
        st.markdown("##### 📊 Top Vendors by Expenditure")
        top_v = analytics.get("top_vendors", [])
        if top_v:
            v_df = pd.DataFrame(top_v).rename(columns={"vendor_name": "Vendor", "total_spent": "Total Spent ($)", "invoice_count": "Invoices"})
            st.bar_chart(v_df.set_index("Vendor")["Total Spent ($)"])
        else:
            st.info("No vendor data available.")

    with c_right:
        st.markdown("##### 📈 Monthly Spend Trend")
        m_trend = analytics.get("monthly_trend", [])
        if m_trend:
            m_df = pd.DataFrame(m_trend).rename(columns={"month_str": "Month", "monthly_spend": "Spend ($)"})
            st.line_chart(m_df.set_index("Month")["Spend ($)"])
        else:
            st.info("No monthly timeline data available.")


# ==============================================================================
# WORKSPACE 11: REPORTS & EXPORTS
# ==============================================================================
def render_reports_exports() -> None:
    st.markdown(
        f"""
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
            <div>
                <h3 style="margin:0; font-weight:800; letter-spacing:-0.02em;">Reports & Exports</h3>
                <div style="font-size:0.8rem; color:{TEXT_MUTED};">Executive audit packages and structured data artifacts with formula injection sanitization</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    invoices = repo.get_invoices(limit=500)
    st.markdown(f"**Export Scope:** Active ledger with {len(invoices)} registered invoices.")

    c1, c2 = st.columns(2, gap="large")

    with c1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div style="font-weight:700; font-size:0.95rem; margin-bottom:0.35rem;">Multi-Sheet Excel Workbook (.xlsx)</div>
                <div style="font-size:0.8rem; color:{TEXT_MUTED}; margin-bottom:0.75rem;">
                    Full audit package containing: Invoices Register, Itemized Line Items, Audit Executive Summary, Validation Exceptions, and Duplicate Review Candidates. Sanitized against formula injection.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        xlsx_bytes = export_to_excel(invoices)
        st.download_button(
            "📥 Download Financial Excel Workbook",
            data=xlsx_bytes,
            file_name="invoice_intelligence_ledger.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    with c2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div style="font-weight:700; font-size:0.95rem; margin-bottom:0.35rem;">Hierarchical Structured JSON</div>
                <div style="font-size:0.8rem; color:{TEXT_MUTED}; margin-bottom:0.75rem;">
                    ERP-compatible JSON payload containing complete metadata, financial breakdowns, and nested itemized line items.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        json_str = export_to_json(invoices)
        st.download_button(
            "📥 Download Structured JSON",
            data=json_str,
            file_name="invoices_payload.json",
            mime="application/json",
            use_container_width=True,
        )

    c3, c4 = st.columns(2, gap="large")
    with c3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div style="font-weight:700; font-size:0.95rem; margin-bottom:0.35rem;">Summary CSV Spreadsheet</div>
                <div style="font-size:0.8rem; color:{TEXT_MUTED}; margin-bottom:0.75rem;">
                    Flattened metadata register of all invoices with vendor, numbers, dates, and amounts.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        csv_summary = export_summary_csv(invoices)
        st.download_button(
            "📥 Download Summary CSV",
            data=csv_summary,
            file_name="invoices_summary.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with c4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div style="font-weight:700; font-size:0.95rem; margin-bottom:0.35rem;">Itemized Line-Items CSV</div>
                <div style="font-size:0.8rem; color:{TEXT_MUTED}; margin-bottom:0.75rem;">
                    Detailed line items catalog linking descriptions, unit prices, and line quantities to parent invoice records.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        csv_items = export_detailed_items_csv(invoices)
        st.download_button(
            "📥 Download Line-Items CSV",
            data=csv_items,
            file_name="invoice_items_detailed.csv",
            mime="text/csv",
            use_container_width=True,
        )


# ==============================================================================
# WORKSPACE 12: ACTIVITY & AUDIT
# ==============================================================================
def render_activity_audit() -> None:
    st.markdown(
        f"""
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
            <div>
                <h3 style="margin:0; font-weight:800; letter-spacing:-0.02em;">Activity & Audit Trail</h3>
                <div style="font-size:0.8rem; color:{TEXT_MUTED};">Immutable system governance trail tracking every document modification and decision</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    act_filter = st.selectbox(
        "Filter by Action Type",
        ["ALL", "CREATION", "STUDIO_EDIT", "USER_EDIT", "RECONCILIATION", "DUPLICATE_REVIEW", "VENDOR_RENAME"],
        index=0,
    )

    logs = repo.get_all_audit_logs(limit=200, action_filter=act_filter)

    st.markdown(f"<div style='font-size:0.8rem; color:{TEXT_MUTED}; margin-bottom:0.75rem;'>Showing {len(logs)} immutable audit events</div>", unsafe_allow_html=True)

    if not logs:
        st.info("No audit logs matching this action filter.")
        return

    log_rows = []
    for l in logs:
        log_rows.append({
            "Audit ID": l.get("id"),
            "Invoice #": l.get("invoice_number") or f"ID #{l.get('invoice_id')}",
            "Vendor": l.get("vendor_name") or "-",
            "Action": l.get("action"),
            "Field": l.get("field_name"),
            "Old Value": l.get("old_value") or "-",
            "New Value": l.get("new_value") or "-",
            "Timestamp": l.get("changed_at"),
        })

    st.dataframe(pd.DataFrame(log_rows), use_container_width=True, hide_index=True)


# ==============================================================================
# WORKSPACE 13: SETTINGS
# ==============================================================================
def render_settings() -> None:
    st.markdown(
        f"""
        <div style="margin-bottom:1.25rem;">
            <h3 style="margin:0; font-weight:800; letter-spacing:-0.02em;">System Settings & Environment</h3>
            <div style="font-size:0.8rem; color:{TEXT_MUTED}; margin-top:0.25rem;">Document engine capabilities, relational storage metrics, and sample invoice resets</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c_diag1, c_diag2 = st.columns(2, gap="large")

    with c_diag1:
        st.markdown(
            f"""
            <div class="metric-card" style="margin-bottom:1.15rem;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.75rem;">
                    <div style="font-weight:700; font-size:0.95rem;">Document Extraction Engine</div>
                    <span class="status-badge status-success">OPERATIONAL</span>
                </div>
                <div style="font-size:0.8rem; color:{TEXT_MUTED}; line-height:1.5;">
                    High-accuracy optical text recognition and multi-stage entity parsing active.
                </div>
                <div style="border-top:1px solid {BORDER_COLOR}; margin:0.85rem 0; padding-top:0.85rem;">
                    <div style="display:flex; justify-content:space-between; font-size:0.8rem; margin-bottom:0.35rem;">
                        <span style="color:{TEXT_MUTED};">Supported Formats:</span>
                        <span style="font-weight:600;">PDF, PNG, JPG, JPEG, TIFF, BMP</span>
                    </div>
                    <div style="display:flex; justify-content:space-between; font-size:0.8rem; margin-bottom:0.35rem;">
                        <span style="color:{TEXT_MUTED};">Extraction Engines:</span>
                        <span style="font-weight:600;">OCR + Heuristic NLP Parser</span>
                    </div>
                    <div style="display:flex; justify-content:space-between; font-size:0.8rem;">
                        <span style="color:{TEXT_MUTED};">Arithmetic Reconciliation:</span>
                        <span style="font-weight:600; color:{PRIMARY_ACCENT};">Subtotal + Tax + Shipping = Total</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div class="metric-card">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.75rem;">
                    <div style="font-weight:700; font-size:0.95rem;">Rule Validation & Security</div>
                    <span class="status-badge status-success">ACTIVE</span>
                </div>
                <div style="font-size:0.8rem; color:{TEXT_MUTED}; line-height:1.5;">
                    Continuous verification of invoice chronology, mandatory fields, and duplicate candidates.
                </div>
                <div style="border-top:1px solid {BORDER_COLOR}; margin:0.85rem 0; padding-top:0.85rem;">
                    <div style="display:flex; justify-content:space-between; font-size:0.8rem; margin-bottom:0.35rem;">
                        <span style="color:{TEXT_MUTED};">Validation Rules:</span>
                        <span style="font-weight:600;">6 Core Integrity Rules</span>
                    </div>
                    <div style="display:flex; justify-content:space-between; font-size:0.8rem;">
                        <span style="color:{TEXT_MUTED};">Duplicate Detection:</span>
                        <span style="font-weight:600;">Multi-Signal Exact & Fuzzy Matching</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c_diag2:
        analytics = repo.get_analytics_summary()
        total_inv = analytics.get("total_invoices", 0)
        total_items = analytics.get("total_items", 0)
        total_spent = analytics.get("total_spend", 0.0)

        st.markdown(
            f"""
            <div class="metric-card" style="margin-bottom:1.15rem;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.75rem;">
                    <div style="font-weight:700; font-size:0.95rem;">Financial Ledger & Ledger DB</div>
                    <span class="status-badge status-success">CONNECTED</span>
                </div>
                <div style="font-size:0.8rem; color:{TEXT_MUTED}; line-height:1.5;">
                    Structured ledger storing normalized invoices, vendor records, itemized line items, and audit history.
                </div>
                <div style="border-top:1px solid {BORDER_COLOR}; margin:0.85rem 0; padding-top:0.85rem;">
                    <div style="display:flex; justify-content:space-between; font-size:0.8rem; margin-bottom:0.35rem;">
                        <span style="color:{TEXT_MUTED};">Registered Invoices:</span>
                        <span style="font-weight:700; font-family:'JetBrains Mono',monospace;">{total_inv}</span>
                    </div>
                    <div style="display:flex; justify-content:space-between; font-size:0.8rem; margin-bottom:0.35rem;">
                        <span style="color:{TEXT_MUTED};">Itemized Lines Stored:</span>
                        <span style="font-weight:700; font-family:'JetBrains Mono',monospace;">{total_items}</span>
                    </div>
                    <div style="display:flex; justify-content:space-between; font-size:0.8rem;">
                        <span style="color:{TEXT_MUTED};">Total Ledger Volume:</span>
                        <span style="font-weight:700; font-family:'JetBrains Mono',monospace; color:{PRIMARY_ACCENT};">${total_spent:,.2f}</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div class="metric-card">
                <div style="font-weight:700; font-size:0.95rem; margin-bottom:0.35rem;">Sample Invoices & Demo Reset</div>
                <div style="font-size:0.8rem; color:{TEXT_MUTED}; line-height:1.5; margin-bottom:0.85rem;">
                    Restore the local ledger to clean synthetic sample invoices across multiple vendor types and scenarios.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("🔄 Reset to Default Sample Invoices", type="secondary", use_container_width=True):
            import subprocess
            subprocess.run([".venv/Scripts/python.exe", "scripts/seed_database.py"], capture_output=True)
            st.success("Ledger refreshed with default sample invoices.")
            st.rerun()


# ==============================================================================
# MAIN ROUTING DISPATCHER
# ==============================================================================
PAGE_DISPATCHER = {
    "Overview": render_overview,
    "My Work Queue": render_work_queue,
    "All Invoices": render_all_invoices,
    "Vendors": render_vendors,
    "Import Center": render_import_center,
    "Extraction Studio": render_extraction_studio,
    "Validation & Exceptions": render_validation_center,
    "Duplicate Review": render_duplicate_review,
    "Reconciliation": render_reconciliation,
    "Financial Insights": render_financial_insights,
    "Reports & Exports": render_reports_exports,
    "Activity & Audit": render_activity_audit,
    "Settings": render_settings,
}

active_renderer = PAGE_DISPATCHER.get(st.session_state.nav_section, render_overview)
active_renderer()
