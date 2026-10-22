"""Computer Vision Preprocessing Pipeline for Invoice Document OCR.

Includes deskewing, grayscale conversion, adaptive thresholding,
bilateral noise reduction, and high-DPI resolution scaling using OpenCV and Pillow.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any, Dict, Tuple, Union

import cv2
import numpy as np
from PIL import Image

ImageInput = Union[str, Path, bytes, Image.Image, np.ndarray]


class ImagePreprocessor:
    """Preprocesses scanned and photographed invoice documents to optimize OCR accuracy."""

    @staticmethod
    def load_as_cv2(image_input: ImageInput) -> np.ndarray:
        """Convert various input formats (path, bytes, PIL, numpy) into a standard BGR/RGB cv2 image."""
        if isinstance(image_input, (str, Path)):
            path = Path(image_input)
            if not path.is_file():
                raise FileNotFoundError(f"Image file not found: {path}")
            # Use imdecode to safely support Unicode paths on Windows
            data = np.fromfile(str(path), dtype=np.uint8)
            img = cv2.imdecode(data, cv2.IMREAD_COLOR)
            if img is None:
                raise ValueError(f"Could not decode image at {path}")
            return img

        if isinstance(image_input, bytes):
            nparr = np.frombuffer(image_input, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                raise ValueError("Could not decode image from bytes.")
            return img

        if isinstance(image_input, Image.Image):
            # PIL Image to BGR numpy array
            rgb_img = image_input.convert("RGB")
            np_img = np.array(rgb_img)
            return cv2.cvtColor(np_img, cv2.COLOR_RGB2BGR)

        if isinstance(image_input, np.ndarray):
            if len(image_input.shape) == 2:
                # Grayscale to BGR
                return cv2.cvtColor(image_input, cv2.COLOR_GRAY2BGR)
            return image_input.copy()

        raise TypeError(f"Unsupported image input type: {type(image_input)}")

    @staticmethod
    def to_grayscale(img: np.ndarray) -> np.ndarray:
        """Convert BGR image to single-channel 8-bit grayscale."""
        if len(img.shape) == 2:
            return img
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    @staticmethod
    def rescale(img: np.ndarray, target_dpi_factor: float = 1.5) -> np.ndarray:
        """Upscale image using bicubic interpolation to improve OCR on small font receipts and tables."""
        if target_dpi_factor <= 1.0:
            return img
        h, w = img.shape[:2]
        new_w = int(w * target_dpi_factor)
        new_h = int(h * target_dpi_factor)
        return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_CUBIC)

    @staticmethod
    def denoise(img: np.ndarray) -> np.ndarray:
        """Remove sensor grain and background paper speckles while preserving sharp text edges."""
        if len(img.shape) == 2:
            # Grayscale bilateral filter
            return cv2.bilateralFilter(img, d=9, sigmaColor=75, sigmaSpace=75)
        # Color bilateral filter
        return cv2.bilateralFilter(img, d=9, sigmaColor=75, sigmaSpace=75)

    @classmethod
    def calculate_skew_angle(cls, gray_img: np.ndarray) -> float:
        """Detect dominant skew angle of text lines using minimum bounding box of thresholded foreground."""
        # Invert: text should be white, background black
        thresh = cv2.threshold(gray_img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

        # Find all foreground coordinates
        coords = np.column_stack(np.where(thresh > 0))
        if len(coords) < 100:
            return 0.0

        angle = cv2.minAreaRect(coords)[-1]

        # Adjust angle from cv2.minAreaRect coordinate convention
        if angle < -45:
            angle = -(90 + angle)
        elif angle > 45:
            angle = 90 - angle
        else:
            angle = -angle

        # Filter out extreme rotations (e.g. vertical layout or noisy calculation)
        if abs(angle) > 30.0:
            return 0.0

        return float(angle)

    @classmethod
    def deskew(cls, img: np.ndarray) -> Tuple[np.ndarray, float]:
        """Rotate image to correct scan skew."""
        gray = cls.to_grayscale(img)
        angle = cls.calculate_skew_angle(gray)

        if abs(angle) < 0.3:
            return img, 0.0

        h, w = img.shape[:2]
        center = (w // 2, h // 2)
        rot_mat = cv2.getRotationMatrix2D(center, angle, 1.0)
        deskewed = cv2.warpAffine(
            img,
            rot_mat,
            (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE,
        )
        return deskewed, angle

    @staticmethod
    def binarize_otsu(gray_img: np.ndarray) -> np.ndarray:
        """Apply Otsu's optimal global thresholding."""
        return cv2.threshold(gray_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

    @staticmethod
    def binarize_adaptive(gray_img: np.ndarray) -> np.ndarray:
        """Apply adaptive Gaussian thresholding for documents with uneven lighting or shadows."""
        return cv2.adaptiveThreshold(
            gray_img,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            blockSize=25,
            C=11,
        )

    @classmethod
    def process_pipeline(
        cls,
        image_input: ImageInput,
        mode: str = "standard",
        auto_deskew: bool = True,
        upscale_factor: float = 1.5,
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Execute end-to-end preprocessing pipeline.

        Modes:
            - 'standard': Grayscale -> Deskew -> Denoise -> Otsu Binarization (best for general invoices)
            - 'adaptive': Grayscale -> Deskew -> Denoise -> Adaptive Gaussian Binarization (best for shadows/photos)
            - 'grayscale_only': Grayscale -> Deskew -> Denoise -> Upscale (keeps anti-aliased font strokes)
            - 'none': Returns raw loaded image without alteration.
        """
        raw_bgr = cls.load_as_cv2(image_input)
        metadata: Dict[str, Any] = {
            "mode": mode,
            "original_shape": raw_bgr.shape,
            "skew_angle": 0.0,
            "upscaled": False,
        }

        if mode == "none":
            return raw_bgr, metadata

        # 1. Deskew
        working_img = raw_bgr
        if auto_deskew:
            working_img, angle = cls.deskew(working_img)
            metadata["skew_angle"] = round(angle, 2)

        # 2. Rescale for small text recognition
        if upscale_factor > 1.0:
            working_img = cls.rescale(working_img, upscale_factor)
            metadata["upscaled"] = True
            metadata["rescaled_shape"] = working_img.shape

        # 3. Grayscale
        gray = cls.to_grayscale(working_img)

        # 4. Denoise
        denoised = cls.denoise(gray)

        # 5. Thresholding according to mode
        if mode == "standard":
            processed = cls.binarize_otsu(denoised)
        elif mode == "adaptive":
            processed = cls.binarize_adaptive(denoised)
        elif mode == "grayscale_only":
            processed = denoised
        else:
            processed = cls.binarize_otsu(denoised)

        metadata["final_shape"] = processed.shape
        return processed, metadata

    @staticmethod
    def to_pil(img_np: np.ndarray) -> Image.Image:
        """Convert OpenCV array (grayscale or BGR) to PIL Image."""
        if len(img_np.shape) == 2:
            return Image.fromarray(img_np, mode="L")
        rgb = cv2.cvtColor(img_np, cv2.COLOR_BGR2RGB)
        return Image.fromarray(rgb, mode="RGB")
