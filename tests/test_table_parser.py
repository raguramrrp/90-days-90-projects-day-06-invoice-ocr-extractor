"""Unit tests for Table Parser and Line Item Extraction."""

from __future__ import annotations

import pytest

from src.parser.table_parser import TableParser


def test_parse_multi_column_items():
    lines = [
        "Description Qty Unit Price Total Amount",
        "Dell UltraSharp 27 4K Monitor 2 $450.00 $900.00",
        "Ergonomic Mechanical Keyboard 3 $85.00 $255.00",
        "Subtotal: $1,155.00",
    ]
    items = TableParser.parse_items(lines)
    assert len(items) == 2
    assert items[0]["description"] == "Dell UltraSharp 27 4K Monitor"
    assert items[0]["quantity"] == 2.0
    assert items[0]["unit_price"] == 450.00
    assert items[0]["amount"] == 900.00

    assert items[1]["description"] == "Ergonomic Mechanical Keyboard"
    assert items[1]["quantity"] == 3.0
    assert items[1]["amount"] == 255.00


def test_parse_single_amount_service():
    lines = [
        "Description Total Amount",
        "Cloud Hosting Standard Tier (Monthly) $450.00",
        "Subtotal: $450.00",
    ]
    items = TableParser.parse_items(lines)
    assert len(items) == 1
    assert items[0]["description"] == "Cloud Hosting Standard Tier (Monthly)"
    assert items[0]["amount"] == 450.00
    assert items[0]["quantity"] == 1.0


def test_ignore_terminator_lines():
    lines = [
        "Description Amount",
        "Item Alpha 100.00",
        "Subtotal: 100.00",
        "Tax: 10.00",
        "Total Amount Due: 110.00",
    ]
    items = TableParser.parse_items(lines)
    assert len(items) == 1
    assert items[0]["description"] == "Item Alpha"
