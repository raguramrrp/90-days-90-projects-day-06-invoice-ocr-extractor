"""Natural Language Processing and Heuristic Helpers for Invoice Fields.

Cleans numeric values, normalizes multi-format dates, maps currencies,
and extracts vendor business entities from top-level document headers.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Optional, Tuple

from dateutil import parser as date_parser

from src.parser.regex_patterns import CURRENCY_MAP

# Words that should never be identified as the Vendor Name
HEADER_STOPWORDS = {
    "INVOICE",
    "TAX INVOICE",
    "COMMERCIAL INVOICE",
    "BILL TO",
    "SOLD TO",
    "SHIP TO",
    "DELIVER TO",
    "CUSTOMER",
    "CLIENT",
    "STATEMENT",
    "RECEIPT",
    "PURCHASE ORDER",
    "DATE",
    "INVOICE DATE",
    "DUE DATE",
    "INVOICE NO",
    "INVOICE NUMBER",
    "TOTAL",
    "SUBTOTAL",
    "AMOUNT",
    "PAGE",
    "DESCRIPTION",
    "QTY",
    "QUANTITY",
    "PRICE",
    "UNIT PRICE",
}

# Common business suffixes
BUSINESS_SUFFIXES = [
    "inc", "inc.", "llc", "ltd", "ltd.", "corp", "corp.", "corporation",
    "technologies", "tech", "systems", "solutions", "services", "enterprises",
    "hardware", "software", "labs", "consulting", "partners", "logistics",
    "supplies", "group", "co", "co.", "company", "holdings"
]


def clean_amount(raw_val: str) -> Tuple[Optional[float], Optional[str]]:
    """Parse raw financial string into numeric float and ISO currency code.

    Examples:
        "$1,250.50" -> (1250.50, "USD")
        "€ 450.00"  -> (450.00, "EUR")
        "1500"      -> (1500.00, None)
    """
    if not raw_val:
        return None, None

    val_str = raw_val.strip()

    # Detect currency
    detected_currency: Optional[str] = None
    for sym, iso in CURRENCY_MAP.items():
        if sym in val_str.upper():
            detected_currency = iso
            break

    # Strip currency signs, commas, extra whitespace
    cleaned = re.sub(r"[^0-9.,]", "", val_str)

    # Handle European comma as decimal (e.g. 1.250,50 vs 1,250.50)
    if "," in cleaned and "." in cleaned:
        if cleaned.rfind(",") > cleaned.rfind("."):
            # Comma is decimal separator (1.250,50)
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            # Period is decimal separator (1,250.50)
            cleaned = cleaned.replace(",", "")
    elif "," in cleaned and "." not in cleaned:
        # Check if comma is decimal (e.g., 50,00) or thousand (e.g. 1,000)
        parts = cleaned.split(",")
        if len(parts) == 2 and len(parts[1]) == 2:
            cleaned = cleaned.replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")

    try:
        num = float(cleaned)
        return round(num, 2), detected_currency
    except ValueError:
        return None, detected_currency


def parse_date_to_iso(raw_date_str: str) -> Optional[str]:
    """Parse arbitrary date string into standard ISO format (YYYY-MM-DD)."""
    if not raw_date_str:
        return None

    # Clean whitespace and trailing punctuation
    clean_str = re.sub(r"[\n\r\t]+", " ", raw_date_str).strip()
    clean_str = clean_str.strip(":.,-")

    # Filter out obvious non-dates
    if len(clean_str) < 6 or not any(char.isdigit() for char in clean_str):
        return None

    try:
        # fuzzy=True ignores prefix/suffix words
        dt = date_parser.parse(clean_str, fuzzy=True, default=datetime(2026, 1, 1))
        # Ensure year is reasonable
        if 2000 <= dt.year <= 2035:
            return dt.strftime("%Y-%m-%d")
        return None
    except Exception:
        return None


def extract_vendor_heuristic(raw_lines: list[str]) -> Tuple[str, float]:
    """Extract vendor entity name using top-section layout heuristics and business suffixes.

    Returns:
        vendor_name: Extracted company name
        confidence: Confidence score between 0.0 and 1.0
    """
    if not raw_lines:
        return "Unknown Vendor", 0.0

    # Look primarily at the top 12 lines of the document
    top_lines = [line.strip() for line in raw_lines[:12] if line.strip()]

    candidate_scores: list[Tuple[str, float]] = []

    for i, line in enumerate(top_lines):
        line_upper = line.upper()

        # Reject lines containing pure stopwords or email/phone/website
        if line_upper in HEADER_STOPWORDS:
            continue
        if any(term in line_upper for term in ["BILL TO", "SHIP TO", "DELIVER TO", "WWW.", "HTTP", "@", "PHONE:", "TEL:"]):
            continue
        if line.startswith("#") or line_upper.startswith("INV"):
            continue

        # Score line based on length, capitalization, business suffix, and position
        words = line.split()
        if len(words) < 1 or len(words) > 7:
            continue

        score = 0.5  # Base score for top-header line

        # Earlier lines are more likely to be vendor name / logo text
        if i == 0:
            score += 0.25
        elif i <= 2:
            score += 0.15

        # Check for presence of business suffix (LLC, Inc, Technologies, etc.)
        has_suffix = any(w.lower().rstrip(".,") in BUSINESS_SUFFIXES for w in words)
        if has_suffix:
            score += 0.25

        # Check title case or upper case
        if line.istitle() or line.isupper():
            score += 0.1

        # Penalize if it contains numbers or date formats
        if any(char.isdigit() for char in line):
            score -= 0.2

        score = min(max(score, 0.0), 0.98)
        candidate_scores.append((line, score))

    if not candidate_scores:
        return "Unknown Vendor", 0.0

    # Pick candidate with highest score
    candidate_scores.sort(key=lambda x: x[1], reverse=True)
    best_candidate, best_score = candidate_scores[0]

    # Clean any trailing colon or punctuation and strip document titles if joined on same line
    clean_vendor = best_candidate.strip(" :,.-")
    clean_vendor = re.sub(r"\s*(?:TAX\s*)?(?:COMMERCIAL\s*)?INVOICE\s*$", "", clean_vendor, flags=re.IGNORECASE)
    clean_vendor = clean_vendor.strip(" :,.-")
    return clean_vendor, round(best_score, 2)
