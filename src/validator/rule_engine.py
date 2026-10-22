"""Rules-based Validation and Exception Engine for Invoices.

Evaluates invoices against financial business rules and outputs structured
ValidationFinding objects containing severity, current values, explanations,
and actionable suggestions for finance operators.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ValidationFinding:
    """Represents a discrete validation exception or audit issue."""
    invoice_id: Optional[int]
    invoice_ref: str
    rule_id: str
    field: str
    severity: str  # 'CRITICAL', 'WARNING', 'INFO'
    current_value: Optional[str]
    explanation: str
    suggested_action: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ValidationRuleEngine:
    """Deterministic, rules-based validation engine for invoice processing."""

    @classmethod
    def evaluate_invoice(
        cls,
        invoice: Dict[str, Any],
        items: Optional[List[Dict[str, Any]]] = None,
        is_duplicate: bool = False,
    ) -> List[ValidationFinding]:
        """Evaluate a single invoice against all financial and structural rules."""
        findings: List[ValidationFinding] = []
        inv_id = invoice.get("id")
        inv_ref = invoice.get("invoice_number") or invoice.get("filename") or f"Record #{inv_id or 'Draft'}"

        vendor = invoice.get("vendor_name")
        inv_no = invoice.get("invoice_number")
        inv_date = invoice.get("invoice_date")
        due_date = invoice.get("due_date")
        subtotal = float(invoice.get("subtotal", 0.0) or 0.0)
        tax = float(invoice.get("tax_amount", 0.0) or 0.0)
        shipping = float(invoice.get("shipping_amount", 0.0) or 0.0)
        discount = float(invoice.get("discount_amount", 0.0) or 0.0)
        total = float(invoice.get("total_amount", 0.0) or 0.0)
        line_items = items if items is not None else invoice.get("line_items", [])

        # Rule 1: Missing Vendor
        if not vendor or str(vendor).strip().lower() in ("unknown", "unknown vendor", "n/a", ""):
            findings.append(
                ValidationFinding(
                    invoice_id=inv_id,
                    invoice_ref=inv_ref,
                    rule_id="RULE_MISSING_VENDOR",
                    field="vendor_name",
                    severity="CRITICAL",
                    current_value=str(vendor or "None"),
                    explanation="Vendor identity could not be reliably recognized in document header.",
                    suggested_action="Specify the legal vendor name in Extraction Studio.",
                )
            )

        # Rule 2: Missing Invoice Number
        if not inv_no or str(inv_no).strip().upper() in ("N/A", "NONE", "UNKNOWN", ""):
            findings.append(
                ValidationFinding(
                    invoice_id=inv_id,
                    invoice_ref=inv_ref,
                    rule_id="RULE_MISSING_INVOICE_NO",
                    field="invoice_number",
                    severity="CRITICAL",
                    current_value=str(inv_no or "None"),
                    explanation="Invoice number identifier is missing or unrecognized.",
                    suggested_action="Locate and enter the invoice or billing reference number.",
                )
            )

        # Rule 3: Missing Invoice Date
        if not inv_date or str(inv_date).strip() in ("", "None"):
            findings.append(
                ValidationFinding(
                    invoice_id=inv_id,
                    invoice_ref=inv_ref,
                    rule_id="RULE_MISSING_DATE",
                    field="invoice_date",
                    severity="CRITICAL",
                    current_value=None,
                    explanation="Invoice issuance date was not detected or parsed.",
                    suggested_action="Enter the document date in YYYY-MM-DD format.",
                )
            )

        # Rule 4: Total Amount Missing or Zero
        if total <= 0.0:
            findings.append(
                ValidationFinding(
                    invoice_id=inv_id,
                    invoice_ref=inv_ref,
                    rule_id="RULE_ZERO_TOTAL",
                    field="total_amount",
                    severity="CRITICAL",
                    current_value=f"{total:.2f}",
                    explanation="Total amount is zero or negative.",
                    suggested_action="Verify the grand total payable on the invoice document.",
                )
            )

        # Rule 5: Date Chronology (Due Date before Invoice Date)
        if inv_date and due_date and due_date < inv_date:
            findings.append(
                ValidationFinding(
                    invoice_id=inv_id,
                    invoice_ref=inv_ref,
                    rule_id="RULE_DATE_CHRONOLOGY",
                    field="due_date",
                    severity="WARNING",
                    current_value=f"Issue: {inv_date}, Due: {due_date}",
                    explanation=f"Due date ({due_date}) precedes invoice date ({inv_date}).",
                    suggested_action="Check if dates are inverted or if invoice terms specify immediate payment.",
                )
            )

        # Rule 6: Accounting Equation Balance
        if total > 0 and subtotal > 0:
            calculated_total = round(subtotal + tax + shipping - discount, 2)
            discrepancy = round(total - calculated_total, 2)
            if abs(discrepancy) > 0.05:
                findings.append(
                    ValidationFinding(
                        invoice_id=inv_id,
                        invoice_ref=inv_ref,
                        rule_id="RULE_MATH_IMBALANCE",
                        field="total_amount",
                        severity="CRITICAL",
                        current_value=f"Extracted: {total:.2f}, Calc: {calculated_total:.2f}",
                        explanation=f"Mathematical imbalance: Total ({total:.2f}) differs from Subtotal + Tax + Shipping - Discount ({calculated_total:.2f}) by {discrepancy:+.2f}.",
                        suggested_action="Reconcile item amounts, tax rates, or shipping charges.",
                    )
                )

        # Rule 7: Line-Items vs Subtotal
        if line_items and subtotal > 0:
            items_sum = round(sum(float(i.get("amount", 0.0) or 0.0) for i in line_items), 2)
            diff = round(items_sum - subtotal, 2)
            if abs(diff) > 0.05:
                findings.append(
                    ValidationFinding(
                        invoice_id=inv_id,
                        invoice_ref=inv_ref,
                        rule_id="RULE_ITEMS_SUBTOTAL_MISMATCH",
                        field="subtotal",
                        severity="WARNING",
                        current_value=f"Items: {items_sum:.2f}, Subtotal: {subtotal:.2f}",
                        explanation=f"Sum of item lines ({items_sum:.2f}) differs from invoice subtotal ({subtotal:.2f}) by {diff:+.2f}.",
                        suggested_action="Check for missing line items or additional unparsed surcharges.",
                    )
                )

        # Rule 8: Line-Item Row Arithmetic
        for idx, item in enumerate(line_items):
            qty = float(item.get("quantity", 1.0) or 1.0)
            price = float(item.get("unit_price", 0.0) or 0.0)
            amount = float(item.get("amount", 0.0) or 0.0)
            if qty > 0 and price > 0 and amount > 0:
                expected_row = round(qty * price, 2)
                if abs(amount - expected_row) > 0.05:
                    findings.append(
                        ValidationFinding(
                            invoice_id=inv_id,
                            invoice_ref=inv_ref,
                            rule_id="RULE_LINE_ITEM_ARITHMETIC",
                            field=f"line_items[{idx}]",
                            severity="INFO",
                            current_value=f"Qty {qty} × ${price:.2f} = ${expected_row:.2f} (Stated: ${amount:.2f})",
                            explanation=f"Line item '{item.get('description', f'Row {idx+1}')}' row math differs by {amount - expected_row:+.2f}.",
                            suggested_action="Verify if a line discount or tax is embedded in the line total.",
                        )
                    )

        # Rule 9: Potential Duplicate
        if is_duplicate or invoice.get("is_duplicate") == 1:
            findings.append(
                ValidationFinding(
                    invoice_id=inv_id,
                    invoice_ref=inv_ref,
                    rule_id="RULE_POTENTIAL_DUPLICATE",
                    field="invoice_number",
                    severity="CRITICAL",
                    current_value=inv_ref,
                    explanation="Invoice matches existing record in database by vendor/number/date.",
                    suggested_action="Review in Duplicate Review workspace before approving payment.",
                )
            )

        return findings

    @classmethod
    def evaluate_all(cls, invoices: List[Dict[str, Any]]) -> List[ValidationFinding]:
        """Evaluate a collection of invoices and aggregate all findings."""
        all_findings: List[ValidationFinding] = []
        for inv in invoices:
            items = inv.get("line_items", [])
            findings = cls.evaluate_invoice(inv, items=items, is_duplicate=(inv.get("is_duplicate") == 1))
            all_findings.extend(findings)
        return all_findings
