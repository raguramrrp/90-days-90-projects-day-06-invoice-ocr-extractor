"""Comprehensive Field Extractor for Invoices.

Applies multi-stage NLP heuristics and regular expression engines
to extract structured entities, dates, totals, and line items.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from src.parser import regex_patterns as rp
from src.parser.nlp_helpers import clean_amount, extract_vendor_heuristic, parse_date_to_iso
from src.parser.table_parser import TableParser


class FieldExtractor:
    """Extracts business entities and financial parameters from OCR text blocks."""

    @classmethod
    def extract_all(cls, raw_text: str) -> Dict[str, Any]:
        """Parse raw text and return structured invoice dictionary."""
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

        field_confidences: Dict[str, float] = {}

        # 1. Vendor Name
        vendor, vendor_conf = extract_vendor_heuristic(lines)
        field_confidences["vendor_name"] = vendor_conf

        # 2. Invoice Number
        inv_no, inv_conf = cls._extract_invoice_number(raw_text)
        field_confidences["invoice_number"] = inv_conf

        # 3. Dates
        inv_date, inv_date_conf = cls._extract_invoice_date(raw_text, lines)
        due_date, due_date_conf = cls._extract_due_date(raw_text, lines, inv_date)
        field_confidences["invoice_date"] = inv_date_conf
        field_confidences["due_date"] = due_date_conf

        # 4. Financial Amounts & Currency
        total_amt, total_curr, total_conf = cls._extract_total(raw_text)
        subtotal_amt, subtotal_curr, sub_conf = cls._extract_subtotal(raw_text)
        tax_amt, tax_curr, tax_conf = cls._extract_tax(raw_text)
        ship_amt, ship_curr, ship_conf = cls._extract_shipping(raw_text)
        disc_amt, disc_curr, disc_conf = cls._extract_discount(raw_text)

        field_confidences["total_amount"] = total_conf
        field_confidences["subtotal"] = sub_conf
        field_confidences["tax_amount"] = tax_conf
        field_confidences["shipping_amount"] = ship_conf
        field_confidences["discount_amount"] = disc_conf

        # Currency resolution (most prevalent currency symbol detected)
        currency_candidates = [c for c in [total_curr, subtotal_curr, tax_curr, ship_curr, disc_curr] if c]
        resolved_currency = currency_candidates[0] if currency_candidates else "USD"

        # 5. PO Number & Payment Terms
        po_number, po_conf = cls._extract_po_number(raw_text)
        terms, terms_conf = cls._extract_payment_terms(raw_text)
        field_confidences["po_number"] = po_conf
        field_confidences["payment_terms"] = terms_conf

        # 6. Itemized Table
        line_items = TableParser.parse_items(lines)

        # Reconcile subtotal if omitted but line items exist
        if (subtotal_amt is None or subtotal_amt == 0.0) and line_items:
            computed_sub = sum(item.get("amount", 0.0) for item in line_items)
            if computed_sub > 0:
                subtotal_amt = round(computed_sub, 2)
                field_confidences["subtotal"] = 0.85

        # Reconcile total if omitted but subtotal & tax exist
        if total_amt is None and subtotal_amt is not None:
            computed_total = (subtotal_amt or 0.0) + (tax_amt or 0.0) + (ship_amt or 0.0) - (disc_amt or 0.0)
            if computed_total > 0:
                total_amt = round(computed_total, 2)
                field_confidences["total_amount"] = 0.80

        # Overall weighted confidence score
        weights = {
            "vendor_name": 0.20,
            "invoice_number": 0.25,
            "invoice_date": 0.20,
            "total_amount": 0.25,
            "subtotal": 0.10,
        }
        weighted_conf = sum(
            field_confidences.get(k, 0.5) * w for k, w in weights.items()
        )
        overall_confidence = round(weighted_conf, 2)

        return {
            "vendor_name": vendor,
            "invoice_number": inv_no or "N/A",
            "invoice_date": inv_date,
            "due_date": due_date,
            "currency": resolved_currency,
            "subtotal": subtotal_amt or 0.0,
            "tax_amount": tax_amt or 0.0,
            "shipping_amount": ship_amt or 0.0,
            "discount_amount": disc_amt or 0.0,
            "total_amount": total_amt or 0.0,
            "payment_terms": terms,
            "po_number": po_number,
            "line_items": line_items,
            "field_confidences": field_confidences,
            "overall_confidence": overall_confidence,
        }

    @staticmethod
    def _extract_invoice_number(text: str) -> Tuple[Optional[str], float]:
        """Extract invoice number using prioritized regex rules."""
        for pattern in rp.INVOICE_NUMBER_PATTERNS:
            match = pattern.search(text)
            if match:
                val = match.group(1).strip(" :.-")
                # Filter out pure words like "DATE" or "TOTAL"
                if len(val) >= 3 and not re.match(r"^(?:DATE|TOTAL|TAX|DUE|BILL)$", val, re.IGNORECASE):
                    return val, 0.95
        return None, 0.0

    @staticmethod
    def _extract_po_number(text: str) -> Tuple[Optional[str], float]:
        """Extract Purchase Order reference number."""
        for pattern in rp.PO_PATTERNS:
            match = pattern.search(text)
            if match:
                val = match.group(1).strip(" :.-")
                if len(val) >= 3:
                    return val, 0.90
        return None, 0.0

    @classmethod
    def _extract_invoice_date(cls, text: str, lines: List[str]) -> Tuple[Optional[str], float]:
        """Extract primary invoice issue date."""
        for pattern in rp.INVOICE_DATE_PATTERNS:
            match = pattern.search(text)
            if match:
                iso = parse_date_to_iso(match.group(1))
                if iso:
                    return iso, 0.95

        # Fallback: scan top lines for standalone date patterns
        for line in lines[:15]:
            for g_pat in rp.GENERIC_DATE_PATTERNS:
                m = g_pat.search(line)
                if m:
                    iso = parse_date_to_iso(m.group(1))
                    if iso:
                        return iso, 0.70

        return None, 0.0

    @classmethod
    def _extract_due_date(
        cls, text: str, lines: List[str], invoice_date: Optional[str]
    ) -> Tuple[Optional[str], float]:
        """Extract payment due date."""
        for pattern in rp.DUE_DATE_PATTERNS:
            match = pattern.search(text)
            if match:
                iso = parse_date_to_iso(match.group(1))
                if iso:
                    return iso, 0.95

        # Fallback: check if another date exists that is later than invoice_date
        all_dates: List[str] = []
        for g_pat in rp.GENERIC_DATE_PATTERNS:
            for m in g_pat.finditer(text):
                iso = parse_date_to_iso(m.group(1))
                if iso and iso not in all_dates:
                    all_dates.append(iso)

        if invoice_date and len(all_dates) >= 2:
            for d in all_dates:
                if d > invoice_date:
                    return d, 0.65

        return None, 0.0

    @staticmethod
    def _extract_total(text: str) -> Tuple[Optional[float], Optional[str], float]:
        """Extract grand total financial amount."""
        for pattern in rp.TOTAL_AMOUNT_PATTERNS:
            for match in pattern.finditer(text):
                raw_amt = match.group(1)
                num, curr = clean_amount(raw_amt)
                if num is not None and num > 0:
                    return num, curr, 0.95
        return None, None, 0.0

    @staticmethod
    def _extract_subtotal(text: str) -> Tuple[Optional[float], Optional[str], float]:
        """Extract subtotal amount before taxes."""
        for pattern in rp.SUBTOTAL_PATTERNS:
            match = pattern.search(text)
            if match:
                num, curr = clean_amount(match.group(1))
                if num is not None and num > 0:
                    return num, curr, 0.90
        return None, None, 0.0

    @staticmethod
    def _extract_tax(text: str) -> Tuple[Optional[float], Optional[str], float]:
        """Extract tax / VAT / GST amount."""
        for pattern in rp.TAX_PATTERNS:
            match = pattern.search(text)
            if match:
                num, curr = clean_amount(match.group(1))
                if num is not None:
                    return num, curr, 0.90
        return 0.0, None, 0.50

    @staticmethod
    def _extract_shipping(text: str) -> Tuple[Optional[float], Optional[str], float]:
        """Extract freight or shipping charge."""
        for pattern in rp.SHIPPING_PATTERNS:
            match = pattern.search(text)
            if match:
                num, curr = clean_amount(match.group(1))
                if num is not None:
                    return num, curr, 0.85
        return 0.0, None, 0.50

    @staticmethod
    def _extract_discount(text: str) -> Tuple[Optional[float], Optional[str], float]:
        """Extract promotional or volume discount amount."""
        for pattern in rp.DISCOUNT_PATTERNS:
            match = pattern.search(text)
            if match:
                num, curr = clean_amount(match.group(1))
                if num is not None:
                    return abs(num), curr, 0.85
        return 0.0, None, 0.50

    @staticmethod
    def _extract_payment_terms(text: str) -> Tuple[Optional[str], float]:
        """Extract payment credit terms (e.g. Net 30)."""
        for pattern in rp.PAYMENT_TERMS_PATTERNS:
            match = pattern.search(text)
            if match:
                return match.group(1).title(), 0.90
        return None, 0.0
