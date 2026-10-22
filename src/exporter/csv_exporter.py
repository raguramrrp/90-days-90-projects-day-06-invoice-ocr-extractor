"""CSV Exporter for Invoices and Line Items.

Generates tabular summary spreadsheets and normalized line-item reports using Pandas.
"""

from __future__ import annotations

import io
from typing import Any, Dict, List

import pandas as pd


def export_summary_csv(invoices: List[Dict[str, Any]]) -> str:
    """Generate summary CSV containing top-level invoice metadata and financials."""
    if not invoices:
        return "id,filename,vendor_name,invoice_number,invoice_date,due_date,currency,subtotal,tax_amount,shipping_amount,discount_amount,total_amount,validation_status\n"

    rows: List[Dict[str, Any]] = []
    for inv in invoices:
        rows.append(
            {
                "id": inv.get("id"),
                "filename": inv.get("filename"),
                "vendor_name": inv.get("vendor_name"),
                "invoice_number": inv.get("invoice_number"),
                "invoice_date": inv.get("invoice_date"),
                "due_date": inv.get("due_date"),
                "currency": inv.get("currency", "USD"),
                "subtotal": inv.get("subtotal", 0.0),
                "tax_amount": inv.get("tax_amount", 0.0),
                "shipping_amount": inv.get("shipping_amount", 0.0),
                "discount_amount": inv.get("discount_amount", 0.0),
                "total_amount": inv.get("total_amount", 0.0),
                "payment_terms": inv.get("payment_terms"),
                "po_number": inv.get("po_number"),
                "validation_status": inv.get("validation_status"),
                "created_at": inv.get("created_at"),
            }
        )

    df = pd.DataFrame(rows)
    output = io.StringIO()
    df.to_csv(output, index=False)
    return output.getvalue()


def export_detailed_items_csv(invoices: List[Dict[str, Any]]) -> str:
    """Generate detailed normalized CSV containing individual line items mapped to parent invoice."""
    rows: List[Dict[str, Any]] = []

    for inv in invoices:
        inv_no = inv.get("invoice_number")
        vendor = inv.get("vendor_name")
        currency = inv.get("currency", "USD")
        inv_date = inv.get("invoice_date")
        items = inv.get("line_items", [])

        if not items:
            rows.append(
                {
                    "invoice_number": inv_no,
                    "vendor_name": vendor,
                    "invoice_date": inv_date,
                    "currency": currency,
                    "item_description": "No line items recorded",
                    "quantity": 1.0,
                    "unit_price": inv.get("total_amount", 0.0),
                    "amount": inv.get("total_amount", 0.0),
                }
            )
        else:
            for item in items:
                rows.append(
                    {
                        "invoice_number": inv_no,
                        "vendor_name": vendor,
                        "invoice_date": inv_date,
                        "currency": currency,
                        "item_description": item.get("description", "Item"),
                        "quantity": item.get("quantity", 1.0),
                        "unit_price": item.get("unit_price", 0.0),
                        "amount": item.get("amount", 0.0),
                    }
                )

    df = pd.DataFrame(rows)
    output = io.StringIO()
    df.to_csv(output, index=False)
    return output.getvalue()
