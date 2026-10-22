"""Duplicate Invoice Detection Engine.

Analyzes normalized vendor identities, invoice numbers, dates, and financial totals
across the database to identify exact and suspected duplicate invoices.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

# Pre-compiled regular expressions for high-frequency normalization
_VENDOR_SUFFIX_RE = re.compile(
    r"\b(llc|inc|corp|ltd|corporation|technologies|partners|group|co|company)\b\.?",
    re.IGNORECASE,
)
_VENDOR_CLEAN_RE = re.compile(r"[^a-z0-9]")
_INV_NUM_CLEAN_RE = re.compile(r"[^a-zA-Z0-9]")


class DuplicateDetector:
    """Detects exact and probabilistic duplicate invoice submissions."""

    @staticmethod
    def normalize_vendor(vendor: Optional[str]) -> str:
        """Normalize vendor string for identity matching."""
        if not vendor or vendor.strip().lower() in ("unknown", "unknown vendor", "n/a", ""):
            return ""
        v = vendor.lower().strip()
        # Remove common corporate suffixes
        v = _VENDOR_SUFFIX_RE.sub("", v)
        # Remove special characters
        v = _VENDOR_CLEAN_RE.sub("", v)
        return v.strip()

    @staticmethod
    def normalize_invoice_number(inv_no: Optional[str]) -> str:
        """Normalize invoice number by removing punctuation and whitespace."""
        if not inv_no or inv_no.strip().upper() in ("N/A", "NONE", "UNKNOWN", ""):
            return ""
        clean = _INV_NUM_CLEAN_RE.sub("", inv_no).upper()
        return clean.strip()

    @classmethod
    def check_duplicate(
        cls,
        candidate_invoice: Dict[str, Any],
        existing_invoices: List[Dict[str, Any]],
        current_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Compare candidate invoice against existing database records.

        Returns:
            Dict containing `is_duplicate`, `severity` ('EXACT', 'SUSPECTED', 'NONE'),
            `matching_invoices`, and `reasons`.
        """
        c_vendor = cls.normalize_vendor(candidate_invoice.get("vendor_name"))
        c_number = cls.normalize_invoice_number(candidate_invoice.get("invoice_number"))
        c_date = candidate_invoice.get("invoice_date")
        c_total = float(candidate_invoice.get("total_amount", 0.0) or 0.0)

        matching_records: List[Dict[str, Any]] = []
        reasons: List[str] = []
        severity = "NONE"

        for existing in existing_invoices:
            # Skip comparing invoice against itself if updating
            e_id = existing.get("id")
            if current_id is not None and e_id == current_id:
                continue

            e_vendor = cls.normalize_vendor(existing.get("vendor_name"))
            e_number = cls.normalize_invoice_number(existing.get("invoice_number"))
            e_date = existing.get("invoice_date")
            e_total = float(existing.get("total_amount", 0.0) or 0.0)

            # Rule 1: Exact Duplicate (Same Vendor + Same Invoice Number)
            if c_vendor and e_vendor and c_number and e_number:
                if c_vendor == e_vendor and c_number == e_number:
                    severity = "EXACT"
                    reasons.append(
                        f"Exact Match: Invoice #{existing.get('invoice_number')} from '{existing.get('vendor_name')}' already exists in database (Record #{e_id})."
                    )
                    matching_records.append(existing)
                    continue

            # Rule 2: Suspected Duplicate (Same Vendor + Same Date + Same Total)
            if c_vendor and e_vendor and c_date and e_date and c_total > 0:
                if c_vendor == e_vendor and c_date == e_date and abs(c_total - e_total) < 0.01:
                    if severity != "EXACT":
                        severity = "SUSPECTED"
                    reasons.append(
                        f"Suspected Match: Invoice on {c_date} for ${c_total:,.2f} from '{existing.get('vendor_name')}' already exists (Record #{e_id})."
                    )
                    matching_records.append(existing)

        is_dup = severity in ("EXACT", "SUSPECTED")
        return {
            "is_duplicate": is_dup,
            "severity": severity,
            "matching_invoices": matching_records,
            "reasons": reasons,
        }

    @classmethod
    def find_all_duplicate_pairs(cls, invoices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify all potential duplicate invoice candidate pairs across the database."""
        pairs: List[Dict[str, Any]] = []
        n = len(invoices)

        for i in range(n):
            for j in range(i + 1, n):
                a = invoices[i]
                b = invoices[j]

                v_a = cls.normalize_vendor(a.get("vendor_name"))
                v_b = cls.normalize_vendor(b.get("vendor_name"))
                num_a = cls.normalize_invoice_number(a.get("invoice_number"))
                num_b = cls.normalize_invoice_number(b.get("invoice_number"))
                d_a = a.get("invoice_date")
                d_b = b.get("invoice_date")
                tot_a = float(a.get("total_amount", 0.0) or 0.0)
                tot_b = float(b.get("total_amount", 0.0) or 0.0)

                # Check 1: Exact Duplicate (Same Vendor + Same Invoice Number)
                if v_a and v_b and num_a and num_b and v_a == v_b and num_a == num_b:
                    pairs.append({
                        "invoice_a": a,
                        "invoice_b": b,
                        "match_type": "EXACT",
                        "matching_attributes": ["Vendor Name", "Invoice Number"],
                        "explanation": f"Invoices #{a.get('id')} and #{b.get('id')} share identical normalized vendor ('{a.get('vendor_name')}') and invoice number ('{a.get('invoice_number')}').",
                        "decision": b.get("duplicate_decision") or a.get("duplicate_decision") or "UNREVIEWED",
                    })
                    continue

                # Check 2: Suspected Duplicate (Same Vendor + Same Date + Same Amount)
                if v_a and v_b and d_a and d_b and tot_a > 0 and tot_b > 0:
                    if v_a == v_b and d_a == d_b and abs(tot_a - tot_b) < 0.01:
                        pairs.append({
                            "invoice_a": a,
                            "invoice_b": b,
                            "match_type": "SUSPECTED",
                            "matching_attributes": ["Vendor Name", "Invoice Date", "Total Amount"],
                            "explanation": f"Invoices #{a.get('id')} and #{b.get('id')} share identical vendor, date ({d_a}), and amount (${tot_a:,.2f}) with differing numbers ('{a.get('invoice_number')}' vs '{b.get('invoice_number')}').",
                            "decision": b.get("duplicate_decision") or a.get("duplicate_decision") or "UNREVIEWED",
                        })

        return pairs
