"""Unit tests for OCR Engine and Bounding Box Extraction."""

from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw
import pytest

from src.ocr.engine import OCREngine


@pytest.fixture
def ocr_engine():
    return OCREngine()


def test_engine_availability(ocr_engine):
    assert ocr_engine.is_available() is True
    version = ocr_engine.get_version()
    assert version != "Not Detected"
    assert "5." in version or "4." in version


def test_ocr_text_extraction(ocr_engine):
    # Render an image with known text
    img = Image.new("RGB", (400, 100), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((20, 35), "INVOICE STATEMENT TOTAL BALANCE", fill=(0, 0, 0))

    text = ocr_engine.extract_text(img)
    assert "INVOICE" in text.upper()
    assert "TOTAL" in text.upper()


def test_word_boxes_and_confidence(ocr_engine):
    img = Image.new("RGB", (400, 100), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((20, 30), "Apex Hardware Labs", fill=(0, 0, 0))

    boxes, mean_conf = ocr_engine.extract_word_boxes(img, min_conf=10.0)
    assert len(boxes) > 0
    assert mean_conf > 0.0

    first_box = boxes[0]
    assert "text" in first_box
    assert "conf" in first_box
    assert "x" in first_box
    assert "y" in first_box


def test_draw_visual_boxes(ocr_engine):
    img = Image.new("RGB", (200, 100), color=(255, 255, 255))
    boxes = [
        {"text": "High", "conf": 95.0, "x": 10, "y": 10, "w": 40, "h": 20},
        {"text": "Med", "conf": 65.0, "x": 60, "y": 10, "w": 40, "h": 20},
        {"text": "Low", "conf": 30.0, "x": 110, "y": 10, "w": 40, "h": 20},
    ]
    overlay = ocr_engine.draw_visual_boxes(img, boxes)
    assert isinstance(overlay, Image.Image)
    assert overlay.size == (200, 100)
