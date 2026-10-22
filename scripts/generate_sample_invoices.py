"""Sample Invoice Generator Script.

Programmatically compiles realistic, professional PDF and PNG invoices
using ReportLab and pypdfium2 for immediate out-of-the-box testing and demonstration.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet

import pypdfium2 as pdfium

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "sample_invoices"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SAMPLE_INVOICES_SPEC = [
    {
        "filename_base": "INV-2026-001_Apex_Hardware",
        "vendor": "Apex Hardware Labs LLC",
        "address": "104 Technology Drive, Suite 400, San Jose, CA 95110",
        "email": "billing@apexhardware.io | www.apexhardware.io",
        "invoice_number": "INV-2026-001",
        "po_number": "PO-99120",
        "invoice_date": "2026-10-15",
        "due_date": "2026-11-14",
        "terms": "Net 30",
        "currency": "USD",
        "bill_to": "NextGen AI Robotics Corp\n45 Innovation Way\nAustin, TX 78701",
        "items": [
            ("Dell UltraSharp 27 4K Monitor", 2, 450.00, 900.00),
            ("Ergonomic Mechanical Keyboard", 3, 85.00, 255.00),
            ("USB-C Dual Display Docking Station", 2, 120.00, 240.00),
        ],
        "subtotal": 1395.00,
        "tax": 111.60,
        "shipping": 25.00,
        "discount": 0.00,
        "total": 1531.60,
    },
    {
        "filename_base": "INV-2026-002_CloudScale_Technologies",
        "vendor": "CloudScale Technologies Inc.",
        "address": "742 Evergreen Blvd, Seattle, WA 98101",
        "email": "accounts@cloudscale.net | www.cloudscale.net",
        "invoice_number": "INV-2026-002",
        "po_number": "PO-77215",
        "invoice_date": "2026-10-18",
        "due_date": "2026-10-18",
        "terms": "Due upon receipt",
        "currency": "USD",
        "bill_to": "Quantum Analytics Group\n120 Market Street\nSan Francisco, CA 94105",
        "items": [
            ("Cloud Kubernetes Cluster Hosting (Oct 2026)", 1, 750.00, 750.00),
            ("Managed PostgreSQL High-Availability DB", 1, 350.00, 350.00),
            ("Object Storage 5TB Tier", 1, 100.00, 100.00),
        ],
        "subtotal": 1200.00,
        "tax": 110.00,
        "shipping": 0.00,
        "discount": 100.00,
        "total": 1210.00,
    },
    {
        "filename_base": "INV-2026-003_Quantum_Consulting",
        "vendor": "Quantum Consulting Partners LLP",
        "address": "500 Financial Center, Floor 18, New York, NY 10005",
        "email": "invoicing@quantumpartners.com",
        "invoice_number": "INV-2026-003",
        "po_number": "PO-55019",
        "invoice_date": "2026-10-20",
        "due_date": "2026-11-20",
        "terms": "Net 30",
        "currency": "USD",
        "bill_to": "Venture Horizon Capital\n88 Wall Street\nNew York, NY 10005",
        "items": [
            ("Data Pipeline Architecture Assessment", 20, 150.00, 3000.00),
            ("ML Model Evaluation & Benchmarking", 15, 150.00, 2250.00),
        ],
        "subtotal": 5250.00,
        "tax": 262.50,
        "shipping": 0.00,
        "discount": 0.00,
        "total": 5512.50,
    },
    {
        "filename_base": "INV-2026-004_Metro_Office_Supplies",
        "vendor": "Metro Office Supplies Co.",
        "address": "1200 Commerce Way, Chicago, IL 60607",
        "email": "support@metrooffice.com",
        "invoice_number": "INV-2026-004",
        "po_number": "PO-88421",
        "invoice_date": "2026-10-21",
        "due_date": "2026-11-05",
        "terms": "Net 15",
        "currency": "USD",
        "bill_to": "Apex Engineering Solutions\n350 Lake Shore Dr\nChicago, IL 60611",
        "items": [
            ("Recycled Copy Paper Box (10 Reams)", 5, 42.00, 210.00),
            ("Gel Ink Pen Multi-pack (Box of 24)", 10, 12.50, 125.00),
            ("Heavy Duty Desktop Stapler & Staples", 3, 24.00, 72.00),
        ],
        "subtotal": 407.00,
        "tax": 32.56,
        "shipping": 15.00,
        "discount": 0.00,
        "total": 454.56,
    },
    {
        "filename_base": "INV-2026-005_CyberShield_Security",
        "vendor": "CyberShield Security Solutions",
        "address": "850 Cyber Parkway, Boston, MA 02110",
        "email": "finance@cybershield.sec",
        "invoice_number": "INV-2026-005",
        "po_number": "PO-33104",
        "invoice_date": "2026-10-22",
        "due_date": "2026-11-22",
        "terms": "Net 30",
        "currency": "USD",
        "bill_to": "Global BioTech Innovations\n400 Kendall Square\nCambridge, MA 02142",
        "items": [
            ("Endpoint Protection Annual License (Seats)", 25, 45.00, 1125.00),
            ("Cloud Vulnerability Scanner Pro", 1, 650.00, 650.00),
        ],
        "subtotal": 1775.00,
        "tax": 142.00,
        "shipping": 0.00,
        "discount": 0.00,
        "total": 1917.00,
    },
]


def generate_invoice_pdf(spec: Dict[str, Any], pdf_path: Path) -> None:
    """Generate a clean, structured PDF invoice using ReportLab."""
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "VendorTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1e293b"),
    )
    subtitle_style = ParagraphStyle(
        "VendorSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#64748b"),
    )
    inv_header_style = ParagraphStyle(
        "InvHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        alignment=2,  # Right aligned
        textColor=colors.HexColor("#2563eb"),
    )
    meta_style = ParagraphStyle(
        "MetaText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        alignment=2,
        textColor=colors.HexColor("#334155"),
    )
    bill_to_title = ParagraphStyle(
        "BillToTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#1e293b"),
    )
    bill_to_body = ParagraphStyle(
        "BillToBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#475569"),
    )

    story = []

    # Top Header Row: Vendor on left, INVOICE label + meta on right
    left_header = [
        Paragraph(spec["vendor"], title_style),
        Spacer(1, 4),
        Paragraph(spec["address"], subtitle_style),
        Paragraph(spec["email"], subtitle_style),
    ]

    right_header = [
        Paragraph("TAX INVOICE", inv_header_style),
        Spacer(1, 4),
        Paragraph(f"<b>Invoice No:</b> {spec['invoice_number']}", meta_style),
        Paragraph(f"<b>Invoice Date:</b> {spec['invoice_date']}", meta_style),
        Paragraph(f"<b>Due Date:</b> {spec['due_date']}", meta_style),
        Paragraph(f"<b>PO Number:</b> {spec['po_number']}", meta_style),
        Paragraph(f"<b>Terms:</b> {spec['terms']}", meta_style),
    ]

    header_table = Table(
        [[left_header, right_header]],
        colWidths=[300, 240],
    )
    header_table.setStyle(
        TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
        ])
    )
    story.append(header_table)
    story.append(Spacer(1, 16))

    # Divider Line
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#cbd5e1")))
    story.append(Spacer(1, 12))

    # Bill To Section
    bill_lines = spec["bill_to"].split("\n")
    bill_to_content = [Paragraph("<b>BILL TO:</b>", bill_to_title)] + [
        Paragraph(line, bill_to_body) for line in bill_lines
    ]
    story.append(Table([[bill_to_content]], colWidths=[540]))
    story.append(Spacer(1, 16))

    # Itemized Table
    table_data = [["Description", "Qty", "Unit Price", "Total Amount"]]
    for desc, qty, price, total in spec["items"]:
        table_data.append([
            desc,
            str(qty),
            f"${price:,.2f}",
            f"${total:,.2f}",
        ])

    items_table = Table(table_data, colWidths=[310, 50, 90, 90])
    items_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
            ("TOPPADDING", (0, 0), (-1, 0), 6),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("ALIGN", (0, 0), (0, -1), "LEFT"),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
            ("TOPPADDING", (0, 1), (-1, -1), 6),
            ("LINEBELOW", (0, 0), (-1, 0), 1.2, colors.HexColor("#cbd5e1")),
            ("LINEBELOW", (0, 1), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ])
    )
    story.append(items_table)
    story.append(Spacer(1, 14))

    # Summary Section (Right aligned)
    summary_rows = [
        ["Subtotal:", f"${spec['subtotal']:,.2f}"],
    ]
    if spec.get("discount", 0) > 0:
        summary_rows.append(["Discount:", f"-${spec['discount']:,.2f}"])
    if spec.get("shipping", 0) > 0:
        summary_rows.append(["Shipping & Handling:", f"${spec['shipping']:,.2f}"])
    summary_rows.append(["Tax (VAT/GST):", f"${spec['tax']:,.2f}"])
    summary_rows.append(["Total Amount Due:", f"${spec['total']:,.2f}"])

    summary_table = Table(summary_rows, colWidths=[130, 90])
    summary_table.setStyle(
        TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
            ("FONTNAME", (0, 0), (-1, -2), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            # Total row styling
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, -1), (-1, -1), 11),
            ("TEXTCOLOR", (0, -1), (-1, -1), colors.HexColor("#0f172a")),
            ("LINEABOVE", (0, -1), (-1, -1), 1.2, colors.HexColor("#1e293b")),
        ])
    )

    # Place summary on right side
    layout_table = Table([["", summary_table]], colWidths=[320, 220])
    layout_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(layout_table)

    story.append(Spacer(1, 24))
    # Footer Notes
    note_style = ParagraphStyle(
        "FooterNote",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#94a3b8"),
        alignment=1,
    )
    story.append(Paragraph("Thank you for your business. Please remit payment via bank transfer referencing the invoice number.", note_style))

    doc.build(story)


def convert_pdf_to_png(pdf_path: Path, png_path: Path) -> None:
    """Render PDF page 1 to high-resolution PNG image."""
    doc = pdfium.PdfDocument(str(pdf_path))
    page = doc[0]
    # Render at 3x scale (~216 DPI) for crystal clear OCR
    bitmap = page.render(scale=3.0)
    pil_img = bitmap.to_pil()
    pil_img.save(str(png_path), format="PNG")
    doc.close()


def generate_all_samples() -> None:
    """Generate all sample PDFs and corresponding PNG images."""
    print(f"Generating {len(SAMPLE_INVOICES_SPEC)} sample invoices in {OUTPUT_DIR}...")
    for spec in SAMPLE_INVOICES_SPEC:
        base_name = spec["filename_base"]
        pdf_file = OUTPUT_DIR / f"{base_name}.pdf"
        png_file = OUTPUT_DIR / f"{base_name}.png"

        generate_invoice_pdf(spec, pdf_file)
        convert_pdf_to_png(pdf_file, png_file)
        print(f"  [OK] Generated: {base_name}.pdf & {base_name}.png")

    print("All sample invoices generated successfully!")


if __name__ == "__main__":
    generate_all_samples()
