"""Pydantic Schema Definitions and Business Rule Validation.

Enforces structural validity, type contracts, and audit ratings for invoice records.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field, field_validator

from src.validator.math_validator import MathValidator


class InvoiceItemSchema(BaseModel):
    """Pydantic schema for an itemized invoice row."""
    description: str = Field(..., min_length=1)
    quantity: float = Field(default=1.0, ge=0.0)
    unit_price: float = Field(default=0.0, ge=0.0)
    amount: float = Field(default=0.0, ge=0.0)


class InvoiceSchema(BaseModel):
    """Pydantic schema for complete structured invoice payload."""
    vendor_name: str = Field(default="Unknown Vendor")
    invoice_number: str = Field(default="N/A")
    invoice_date: Optional[str] = None
    due_date: Optional[str] = None
    currency: str = Field(default="USD", max_length=10)
    subtotal: float = Field(default=0.0, ge=0.0)
    tax_amount: float = Field(default=0.0, ge=0.0)
    shipping_amount: float = Field(default=0.0, ge=0.0)
    discount_amount: float = Field(default=0.0, ge=0.0)
    total_amount: float = Field(default=0.0, ge=0.0)
    payment_terms: Optional[str] = None
    po_number: Optional[str] = None
    line_items: List[InvoiceItemSchema] = Field(default_factory=list)
    overall_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    validation_status: str = Field(default="PENDING")

    @field_validator("vendor_name", mode="before")
    @classmethod
    def clean_vendor(cls, v: Any) -> str:
        if not v or not str(v).strip():
            return "Unknown Vendor"
        return str(v).strip()

    @field_validator("currency", mode="before")
    @classmethod
    def clean_currency(cls, v: Any) -> str:
        if not v:
            return "USD"
        return str(v).strip().upper()


def validate_invoice_payload(payload: Dict[str, Any]) -> Tuple[InvoiceSchema, Dict[str, Any]]:
    """Validate raw extracted invoice dictionary and produce an audit health report."""
    # Convert item dicts to schemas
    items = [
        InvoiceItemSchema(**item) if isinstance(item, dict) else item
        for item in payload.get("line_items", [])
    ]

    clean_payload = {**payload, "line_items": items}
    invoice = InvoiceSchema(**clean_payload)

    # Arithmetic check
    math_result = MathValidator.validate_totals(
        subtotal=invoice.subtotal,
        tax_amount=invoice.tax_amount,
        shipping_amount=invoice.shipping_amount,
        discount_amount=invoice.discount_amount,
        total_amount=invoice.total_amount,
        line_items=[i.model_dump() for i in invoice.line_items],
    )

    # Date order check
    date_warning: Optional[str] = None
    if invoice.invoice_date and invoice.due_date:
        if invoice.due_date < invoice.invoice_date:
            date_warning = (
                f"Due date ({invoice.due_date}) precedes invoice date ({invoice.invoice_date})."
            )

    # Determine overall audit status
    audit_flags: List[str] = list(math_result.get("messages", []))
    if date_warning:
        audit_flags.append(date_warning)

    if invoice.vendor_name == "Unknown Vendor":
        audit_flags.append("Vendor name could not be reliably extracted.")
    if invoice.invoice_number in ("N/A", "", None):
        audit_flags.append("Invoice number missing or unrecognized.")

    # Calculate audit rating
    if math_result["is_valid"] and invoice.vendor_name != "Unknown Vendor" and invoice.invoice_number != "N/A":
        audit_grade = "EXCELLENT"
        invoice.validation_status = "VALIDATED"
    elif math_result["is_valid"]:
        audit_grade = "GOOD"
        invoice.validation_status = "VERIFIED_WITH_WARNINGS"
    else:
        audit_grade = "NEEDS_REVIEW"
        invoice.validation_status = "DISCREPANCY"

    report = {
        "grade": audit_grade,
        "validation_status": invoice.validation_status,
        "math_audit": math_result,
        "date_warning": date_warning,
        "audit_flags": audit_flags,
    }

    return invoice, report
