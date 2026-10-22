"""PDF Document Processor for Invoices.

Handles direct digital text extraction and renders PDF pages into high-DPI
raster images for OCR processing and visual UI preview using pypdf, pdfplumber, and pypdfium2.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any, Dict, List, Union

from PIL import Image
import pdfplumber
import pypdf
import pypdfium2 as pdfium

PDFInput = Union[str, Path, bytes, io.BytesIO]


class PDFProcessor:
    """Utilities for reading, rendering, and extracting digital content from PDF invoices."""

    @staticmethod
    def is_pdf(file_input: PDFInput) -> bool:
        """Check if input is a valid PDF by magic bytes or file extension."""
        if isinstance(file_input, (str, Path)):
            path = Path(file_input)
            if path.suffix.lower() == ".pdf":
                return True
            try:
                with open(path, "rb") as f:
                    header = f.read(5)
                    return header.startswith(b"%PDF-")
            except Exception:
                return False

        if isinstance(file_input, bytes):
            return file_input.startswith(b"%PDF-")

        if isinstance(file_input, io.BytesIO):
            pos = file_input.tell()
            header = file_input.read(5)
            file_input.seek(pos)
            return header.startswith(b"%PDF-")

        return False

    @staticmethod
    def extract_direct_text(file_input: PDFInput) -> str:
        """Extract embedded digital text from PDF. Returns empty string if PDF is scanned or image-only."""
        extracted_pages: List[str] = []

        try:
            # First try pdfplumber for layout-preserving extraction
            if isinstance(file_input, (str, Path)):
                with pdfplumber.open(file_input) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text(layout=True) or ""
                        if page_text.strip():
                            extracted_pages.append(page_text)
            else:
                stream = file_input if isinstance(file_input, io.BytesIO) else io.BytesIO(file_input)
                with pdfplumber.open(stream) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text(layout=True) or ""
                        if page_text.strip():
                            extracted_pages.append(page_text)
        except Exception:
            # Fallback to pypdf
            try:
                stream = (
                    open(file_input, "rb")
                    if isinstance(file_input, (str, Path))
                    else (file_input if isinstance(file_input, io.BytesIO) else io.BytesIO(file_input))
                )
                reader = pypdf.PdfReader(stream)
                for page in reader.pages:
                    text = page.extract_text() or ""
                    if text.strip():
                        extracted_pages.append(text)
                if isinstance(file_input, (str, Path)):
                    stream.close()
            except Exception:
                pass

        return "\n\n".join(extracted_pages).strip()

    @staticmethod
    def convert_to_images(file_input: PDFInput, scale: float = 2.0) -> List[Image.Image]:
        """Render all pages of the PDF to PIL images for OCR and UI preview."""
        images: List[Image.Image] = []

        if isinstance(file_input, (str, Path)):
            doc = pdfium.PdfDocument(str(file_input))
        elif isinstance(file_input, bytes):
            doc = pdfium.PdfDocument(file_input)
        elif isinstance(file_input, io.BytesIO):
            doc = pdfium.PdfDocument(file_input.getvalue())
        else:
            raise TypeError(f"Unsupported PDF input type: {type(file_input)}")

        for page in doc:
            # Render page with 2x scale for sharp text recognition
            bitmap = page.render(scale=scale)
            pil_image = bitmap.to_pil()
            images.append(pil_image)

        doc.close()
        return images

    @classmethod
    def get_first_page_as_image(cls, file_input: PDFInput) -> Image.Image:
        """Render and return the first page of the PDF as a PIL Image."""
        images = cls.convert_to_images(file_input, scale=2.0)
        if not images:
            raise ValueError("No pages found in PDF document.")
        return images[0]

    @staticmethod
    def get_metadata(file_input: PDFInput) -> Dict[str, Any]:
        """Extract metadata from PDF document."""
        stream = (
            open(file_input, "rb")
            if isinstance(file_input, (str, Path))
            else (file_input if isinstance(file_input, io.BytesIO) else io.BytesIO(file_input))
        )
        try:
            reader = pypdf.PdfReader(stream)
            meta = reader.metadata or {}
            num_pages = len(reader.pages)
            return {
                "num_pages": num_pages,
                "title": meta.title,
                "author": meta.author,
                "producer": meta.producer,
                "creation_date": meta.creation_date,
            }
        except Exception as e:
            return {"error": str(e), "num_pages": 0}
        finally:
            if isinstance(file_input, (str, Path)) and not stream.closed:
                stream.close()
