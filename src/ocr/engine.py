"""OCR Engine Orchestrator for Invoice Text and Bounding Box Extraction.

Interfaces with Tesseract OCR, tracks word-level confidence scores,
renders bounding box visualization overlays, and manages fallback mechanisms.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import cv2
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import pytesseract

import config
from src.ocr.pdf_processor import PDFProcessor
from src.ocr.preprocessor import ImagePreprocessor

InvoiceInput = Union[str, Path, bytes, Image.Image, np.ndarray]


class OCREngine:
    """Manages document text extraction and spatial character analysis."""

    def __init__(self, tesseract_cmd: Optional[str] = None):
        """Initialize engine with specified or auto-discovered Tesseract executable."""
        self.cmd = tesseract_cmd or config.TESSERACT_EXECUTABLE
        if self.cmd:
            pytesseract.pytesseract.tesseract_cmd = self.cmd

    def is_available(self) -> bool:
        """Check if Tesseract binary is installed and executable."""
        if not self.cmd:
            return False
        try:
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False

    def get_version(self) -> str:
        """Return the installed Tesseract version."""
        try:
            return str(pytesseract.get_tesseract_version())
        except Exception as e:
            return f"Unavailable ({e})"

    def extract_text(
        self,
        image: Union[Image.Image, np.ndarray],
        psm: int = 4,
        oem: int = 3,
        lang: str = "eng",
    ) -> str:
        """Extract raw text from an image with specified Page Segmentation Mode (PSM).

        Default PSM 4: Assume a single column of text of variable sizes (best for multi-column invoices).
        PSM 3: Fully automatic page segmentation without OSD.
        PSM 6: Assume a single uniform block of text.
        """
        custom_config = f"--oem {oem} --psm {psm}"
        return pytesseract.image_to_string(image, lang=lang, config=custom_config)

    def extract_word_boxes(
        self,
        image: Union[Image.Image, np.ndarray],
        psm: int = 4,
        min_conf: float = 20.0,
    ) -> Tuple[List[Dict[str, Any]], float]:
        """Extract word-level bounding boxes and confidence scores.

        Returns:
            boxes: List of dicts with keys 'text', 'conf', 'x', 'y', 'w', 'h', 'line_num'
            mean_conf: Average confidence across valid words
        """
        custom_config = f"--oem 3 --psm {psm}"
        data = pytesseract.image_to_data(
            image,
            config=custom_config,
            output_type=pytesseract.Output.DATAFRAME,
        )

        boxes: List[Dict[str, Any]] = []
        confidences: List[float] = []

        if data is None or data.empty:
            return boxes, 0.0

        for _, row in data.iterrows():
            text = str(row.get("text", "")).strip()
            conf = float(row.get("conf", -1))

            if text and conf >= min_conf:
                boxes.append(
                    {
                        "text": text,
                        "conf": round(conf, 1),
                        "x": int(row.get("left", 0)),
                        "y": int(row.get("top", 0)),
                        "w": int(row.get("width", 0)),
                        "h": int(row.get("height", 0)),
                        "block_num": int(row.get("block_num", 0)),
                        "line_num": int(row.get("line_num", 0)),
                        "word_num": int(row.get("word_num", 0)),
                    }
                )
                confidences.append(conf)

        mean_conf = round(float(np.mean(confidences)), 1) if confidences else 0.0
        return boxes, mean_conf

    @staticmethod
    def draw_visual_boxes(
        base_image: Union[Image.Image, np.ndarray],
        boxes: List[Dict[str, Any]],
        show_labels: bool = False,
    ) -> Image.Image:
        """Render color-coded bounding boxes on image for UI inspection.

        Green: High confidence (>= 80%)
        Yellow/Orange: Medium confidence (50-79%)
        Red: Low confidence (< 50%)
        """
        if isinstance(base_image, np.ndarray):
            pil_img = ImagePreprocessor.to_pil(base_image).convert("RGB")
        else:
            pil_img = base_image.convert("RGB")

        overlay = pil_img.copy()
        draw = ImageDraw.Draw(overlay)

        for b in boxes:
            x, y, w, h = b["x"], b["y"], b["w"], b["h"]
            conf = b.get("conf", 0.0)

            if conf >= 80:
                color = (46, 204, 113)  # Emerald Green
            elif conf >= 50:
                color = (243, 156, 18)  # Orange / Yellow
            else:
                color = (231, 76, 60)   # Coral Red

            # Draw rectangle with 2px stroke
            draw.rectangle([x, y, x + w, y + h], outline=color, width=2)

            if show_labels and b.get("text"):
                draw.text((x, max(0, y - 12)), b["text"][:10], fill=color)

        return overlay

    def process_document(
        self,
        document_input: InvoiceInput,
        preprocess_mode: str = "standard",
        auto_deskew: bool = True,
        upscale_factor: float = 1.5,
    ) -> Dict[str, Any]:
        """Execute full OCR pipeline on an image or PDF file.

        Returns comprehensive result dictionary with raw text, word coordinates,
        confidence metrics, preview images, and processing telemetry.
        """
        start_time = time.time()

        # Handle PDF vs Image
        is_pdf_doc = PDFProcessor.is_pdf(document_input)
        digital_text = ""
        rendered_pil: Image.Image

        if is_pdf_doc:
            # Try direct text extraction first
            digital_text = PDFProcessor.extract_direct_text(document_input)
            rendered_pil = PDFProcessor.get_first_page_as_image(document_input)
        else:
            rendered_pil = ImagePreprocessor.to_pil(
                ImagePreprocessor.load_as_cv2(document_input)
            )

        # Preprocess image for OCR
        preprocessed_np, preproc_meta = ImagePreprocessor.process_pipeline(
            rendered_pil,
            mode=preprocess_mode,
            auto_deskew=auto_deskew,
            upscale_factor=upscale_factor,
        )
        preprocessed_pil = ImagePreprocessor.to_pil(preprocessed_np)

        # Execute Tesseract OCR
        raw_ocr_text = ""
        boxes: List[Dict[str, Any]] = []
        mean_confidence = 0.0
        engine_used = "Tesseract OCR"

        if self.is_available():
            try:
                raw_ocr_text = self.extract_text(preprocessed_np)
                boxes, mean_confidence = self.extract_word_boxes(preprocessed_np)
            except Exception as e:
                raw_ocr_text = f"OCR Error: {e}"
        else:
            engine_used = "Digital PDF / Fallback (Tesseract Not Installed)"

        # If PDF had clean digital text and OCR failed or had low confidence, merge/prefer digital text
        combined_text = raw_ocr_text
        if digital_text and (len(digital_text.strip()) > len(raw_ocr_text.strip()) or not raw_ocr_text.strip()):
            combined_text = digital_text
            if mean_confidence == 0.0:
                mean_confidence = 95.0

        # Generate visual inspection overlay
        annotated_image = self.draw_visual_boxes(preprocessed_pil, boxes)

        elapsed_seconds = round(time.time() - start_time, 2)

        return {
            "raw_text": combined_text.strip(),
            "digital_text": digital_text.strip(),
            "ocr_text": raw_ocr_text.strip(),
            "word_boxes": boxes,
            "mean_confidence": mean_confidence,
            "engine": engine_used,
            "is_pdf": is_pdf_doc,
            "original_preview": rendered_pil,
            "preprocessed_image": preprocessed_pil,
            "annotated_image": annotated_image,
            "preprocessing_meta": preproc_meta,
            "processing_time_sec": elapsed_seconds,
        }
