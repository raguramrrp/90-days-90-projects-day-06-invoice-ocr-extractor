"""Financial Arithmetic and Balance Validator for Invoices.

Validates that itemized line items sum to subtotal and that
Subtotal + Tax + Shipping - Discount equals the extracted Total Amount.
"""

from __future__ import annotations

from typing import Any, Dict, List


class MathValidator:
    """Verifies mathematical consistency across extracted financial totals."""

    @classmethod
    def validate_totals(
        cls,
        subtotal: float,
        tax_amount: float,
        shipping_amount: float,
        discount_amount: float,
        total_amount: float,
        line_items: List[Dict[str, Any]],
        tolerance: float = 0.05,
    ) -> Dict[str, Any]:
        """Perform comprehensive accounting reconciliation checks."""
        messages: List[str] = []
        is_passed = True

        # 1. Check Line Items vs Subtotal
        line_items_sum = 0.0
        line_items_match = True

        if line_items:
            line_items_sum = round(
                sum(item.get("amount", 0.0) for item in line_items), 2
            )
            if subtotal > 0 and abs(line_items_sum - subtotal) > tolerance:
                diff = round(line_items_sum - subtotal, 2)
                line_items_match = False
                messages.append(
                    f"Line items sum ({line_items_sum:.2f}) differs from subtotal ({subtotal:.2f}) by {diff:+.2f}."
                )
            elif subtotal > 0:
                messages.append(
                    f"Line items sum ({line_items_sum:.2f}) exactly matches subtotal."
                )

        # 2. Check Balance: Subtotal + Tax + Shipping - Discount == Total Amount
        calculated_total = round(
            (subtotal or 0.0)
            + (tax_amount or 0.0)
            + (shipping_amount or 0.0)
            - (discount_amount or 0.0),
            2,
        )

        discrepancy = 0.0
        if total_amount > 0 and subtotal > 0:
            discrepancy = round(total_amount - calculated_total, 2)
            if abs(discrepancy) > tolerance:
                is_passed = False
                messages.append(
                    f"Total mismatch: Extracted total is {total_amount:.2f}, but calculated (Subtotal {subtotal:.2f} + Tax {tax_amount:.2f} + Shipping {shipping_amount:.2f} - Discount {discount_amount:.2f}) is {calculated_total:.2f} (diff: {discrepancy:+.2f})."
                )
            else:
                messages.append(
                    f"Total equation verified: {subtotal:.2f} + {tax_amount:.2f} + {shipping_amount:.2f} - {discount_amount:.2f} = {total_amount:.2f}."
                )
        elif total_amount == 0.0 and subtotal == 0.0:
            is_passed = False
            messages.append("No financial amounts detected in document.")

        status = "PASSED" if (is_passed and total_amount > 0) else "DISCREPANCY"
        if total_amount == 0.0 and subtotal == 0.0:
            status = "INSUFFICIENT_DATA"

        return {
            "status": status,
            "is_valid": is_passed and total_amount > 0,
            "calculated_total": calculated_total,
            "extracted_total": total_amount,
            "discrepancy": discrepancy,
            "line_items_sum": line_items_sum,
            "line_items_match": line_items_match,
            "messages": messages,
        }
