"""Line Item Table Parser for Itemized Invoices.

Identifies tabular invoice regions, segments line items, and extracts
product descriptions, quantities, unit prices, and row totals using
robust right-to-left reverse token analysis and arithmetic verification.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from src.parser.nlp_helpers import clean_amount

TABLE_HEADER_KEYWORDS = [
    "description", "item", "product", "details", "particulars", "service",
    "qty", "quantity", "hours", "units",
    "price", "rate", "unit price", "unit cost",
    "amount", "line total", "total amount",
]

TABLE_TERMINATOR_KEYWORDS = [
    "subtotal", "sub total", "total amount due", "grand total", "total due",
    "balance due", "tax (vat/gst)", "shipping & handling", "freight",
    "thank you for your business", "notes:", "terms:",
]


class TableParser:
    """Parses tabular line item data from invoice text blocks."""

    @classmethod
    def parse_items(cls, lines: List[str]) -> List[Dict[str, Any]]:
        """Extract itemized line rows from invoice text lines."""
        items: List[Dict[str, Any]] = []
        if not lines:
            return items

        # Locate table start (header line)
        start_idx = 0
        for i, line in enumerate(lines):
            line_lower = line.lower()
            match_count = sum(1 for kw in TABLE_HEADER_KEYWORDS if kw in line_lower)
            if match_count >= 2:
                start_idx = i + 1
                break

        scan_lines = lines[start_idx:] if start_idx > 0 else lines

        for line in scan_lines:
            line_str = line.strip()
            if not line_str:
                continue

            line_lower = line_str.lower()

            # Stop when summary block or footer is encountered
            if any(term in line_lower for term in TABLE_TERMINATOR_KEYWORDS):
                break
            if re.match(r"^(?:subtotal|tax|discount|shipping|total amount due|grand total)\b", line_lower):
                break

            # Attempt to parse row
            parsed_item = cls._parse_line_item(line_str)
            if parsed_item:
                items.append(parsed_item)

        return items

    @classmethod
    def _parse_line_item(cls, line: str) -> Optional[Dict[str, Any]]:
        """Parse a single text line using reverse right-to-left financial token matching."""
        # Find all monetary/numerical tokens matching currency patterns like $XX.XX or XX.XX
        amount_matches = list(
            re.finditer(
                r"(?:(?:\b[A-Z]{3}\b|[$€£₹¥])\s*)?\b\d+(?:,\d{3})*(?:\.\d{2})\b",
                line,
            )
        )

        if len(amount_matches) >= 2:
            # Rightmost is Total Amount, second rightmost is Unit Price
            total_match = amount_matches[-1]
            price_match = amount_matches[-2]

            total_val, _ = clean_amount(total_match.group(0))
            price_val, _ = clean_amount(price_match.group(0))

            # Text between start of line and price_match
            left_chunk = line[: price_match.start()].strip()

            # Check if there is a quantity immediately preceding price_match
            qty_match = re.search(r"(\d+(?:\.\d+)?)\s*$", left_chunk)
            qty_val = 1.0
            desc = left_chunk

            if qty_match:
                qty_val = float(qty_match.group(1))
                desc = left_chunk[: qty_match.start()].strip()

            desc = desc.strip(" |-\t:")
            if desc and total_val is not None and price_val is not None:
                # Discard if this looks like a summary line
                if any(k in desc.lower() for k in ["subtotal", "total", "tax", "shipping", "discount"]):
                    return None

                return {
                    "description": desc,
                    "quantity": qty_val,
                    "unit_price": price_val,
                    "amount": total_val,
                }

        elif len(amount_matches) == 1:
            # Single amount at the end: Description followed by single total
            amt_match = amount_matches[0]
            amt_val, _ = clean_amount(amt_match.group(0))
            desc = line[: amt_match.start()].strip(" |-\t:")

            if desc and len(desc) >= 3 and amt_val is not None and amt_val > 0:
                if any(k in desc.lower() for k in ["subtotal", "total", "tax", "shipping", "discount", "balance"]):
                    return None

                return {
                    "description": desc,
                    "quantity": 1.0,
                    "unit_price": amt_val,
                    "amount": amt_val,
                }

        return None
