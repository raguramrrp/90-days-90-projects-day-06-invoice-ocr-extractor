"""Regex Patterns and Keyword Dictionaries for Invoice Field Extraction.

Provides robust, multi-variant regular expressions for parsing invoice numbers,
dates, financial totals, line items, and payment metadata.
"""

import re

# Invoice Number Patterns (ordered by specificity)
INVOICE_NUMBER_PATTERNS = [
    # Explicit labeled forms requiring number/no/#/id
    re.compile(
        r"\b(?:invoice|inv|bill)\s*(?:no|num|number|#|id|code)\s*[:.\-]?\s*([A-Za-z0-9\-/_]{3,25})",
        re.IGNORECASE,
    ),
    re.compile(r"\b(?:invoice\s*identifier)\s*[:.\-]?\s*([A-Za-z0-9\-/_]{3,25})", re.IGNORECASE),
    re.compile(r"\b(INV[-_]?[0-9]{3,10}[A-Za-z0-9\-]*)\b", re.IGNORECASE),
    re.compile(r"\b(?:#\s*([A-Za-z0-9\-]{4,20}))\b", re.IGNORECASE),
]

# Purchase Order Patterns
PO_PATTERNS = [
    re.compile(
        r"(?:p\.?o\.?\s*(?:number|no|#)?|purchase\s*order\s*(?:no|#)?)\s*[:.\-]?\s*([A-Z0-9\-/_]{3,20})",
        re.IGNORECASE,
    )
]

# Date Labelled Patterns
INVOICE_DATE_PATTERNS = [
    re.compile(
        r"(?:invoice\s*date|date\s*of\s*issue|issue\s*date|billing\s*date|dated)\s*[:.\-]?\s*([A-Za-z0-9,/\.\s\-]{6,25})",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bdate\s*[:.\-]?\s*([A-Za-z0-9,/\.\s\-]{6,25})",
        re.IGNORECASE,
    ),
]

DUE_DATE_PATTERNS = [
    re.compile(
        r"(?:due\s*date|payment\s*due|pay\s*by|terms\s*due|due)\s*[:.\-]?\s*([A-Za-z0-9,/\.\s\-]{6,25})",
        re.IGNORECASE,
    )
]

# Standalone Date Recognition Patterns
GENERIC_DATE_PATTERNS = [
    # ISO: 2026-10-22 or 2026/10/22
    re.compile(r"\b(20\d{2}[-/.]\d{1,2}[-/.]\d{1,2})\b"),
    # Standard Numeric: 22/10/2026 or 10/22/2026
    re.compile(r"\b(\d{1,2}[-/.]\d{1,2}[-/.]20\d{2})\b"),
    # Verbal: Oct 22, 2026 or 22 October 2026
    re.compile(
        r"\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+20\d{2})\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?,?\s+20\d{2})\b",
        re.IGNORECASE,
    ),
]

# Financial Amount Regex Component
AMOUNT_REGEX = r"([$€£₹¥A-Z]{0,3}\s*(?:[0-9]{1,3}(?:,[0-9]{3})+|[0-9]+)(?:\.[0-9]{2})?)"

TOTAL_AMOUNT_PATTERNS = [
    # Explicit final balance labels
    re.compile(
        r"(?:total\s*amount\s*due|grand\s*total|total\s*due|balance\s*due|amount\s*due|total\s*payable|net\s*payable)\s*[:.\-]?\s*"
        + AMOUNT_REGEX,
        re.IGNORECASE,
    ),
    # Total with explicit punctuation delimiter (prevents matching 'Total Amount' table column headers)
    re.compile(
        r"(?:total\s*amount|total)\s*[:.\-]\s*" + AMOUNT_REGEX,
        re.IGNORECASE,
    ),
    # Fallback total without punctuation
    re.compile(
        r"\btotal\s+due\s*" + AMOUNT_REGEX,
        re.IGNORECASE,
    ),
]

SUBTOTAL_PATTERNS = [
    re.compile(
        r"(?:subtotal|sub\s*total|net\s*amount|total\s*before\s*tax|sub-total)\s*[:.\-]?\s*"
        + AMOUNT_REGEX,
        re.IGNORECASE,
    )
]

TAX_PATTERNS = [
    re.compile(
        r"(?:tax(?:\s*\([^)]*\))?|vat|gst|sales\s*tax|hst)\s*[:.\-]?\s*"
        + AMOUNT_REGEX,
        re.IGNORECASE,
    )
]

SHIPPING_PATTERNS = [
    re.compile(
        r"(?:shipping(?:\s*&\s*handling)?|freight|delivery|s&h)\s*[:.\-]?\s*"
        + AMOUNT_REGEX,
        re.IGNORECASE,
    )
]

DISCOUNT_PATTERNS = [
    re.compile(
        r"(?:discount|rebate|savings|credit)\s*[:.\-]?\s*-?" + AMOUNT_REGEX,
        re.IGNORECASE,
    )
]

# Payment Terms
PAYMENT_TERMS_PATTERNS = [
    re.compile(r"\b(net\s*15|net\s*30|net\s*45|net\s*60|net\s*90)\b", re.IGNORECASE),
    re.compile(r"\b(due\s*upon\s*receipt|immediate|cash\s*on\s*delivery|cod)\b", re.IGNORECASE),
]

# Currency Symbol to ISO Code Mapping
CURRENCY_MAP = {
    "$": "USD",
    "USD": "USD",
    "US$": "USD",
    "€": "EUR",
    "EUR": "EUR",
    "£": "GBP",
    "GBP": "GBP",
    "₹": "INR",
    "INR": "INR",
    "RS": "INR",
    "RS.": "INR",
    "¥": "JPY",
    "JPY": "JPY",
    "CAD": "CAD",
    "AUD": "AUD",
    "CHF": "CHF",
}
