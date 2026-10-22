"""Unit tests for Computer Vision Image Preprocessor."""

from __future__ import annotations

import numpy as np
from PIL import Image
import pytest

from src.ocr.preprocessor import ImagePreprocessor


def test_load_as_cv2_from_pil():
    pil_img = Image.new("RGB", (100, 50), color=(255, 255, 255))
    cv_img = ImagePreprocessor.load_as_cv2(pil_img)
    assert isinstance(cv_img, np.ndarray)
    assert cv_img.shape == (50, 100, 3)


def test_to_grayscale():
    bgr_img = np.zeros((60, 80, 3), dtype=np.uint8)
    gray = ImagePreprocessor.to_grayscale(bgr_img)
    assert len(gray.shape) == 2
    assert gray.shape == (60, 80)


def test_rescale():
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    upscaled = ImagePreprocessor.rescale(img, target_dpi_factor=2.0)
    assert upscaled.shape == (200, 200, 3)


def test_binarize_otsu():
    gray = np.array([[10, 20], [200, 240]], dtype=np.uint8)
    binary = ImagePreprocessor.binarize_otsu(gray)
    assert set(np.unique(binary)).issubset({0, 255})


def test_pipeline_modes():
    pil_img = Image.new("RGB", (120, 80), color=(240, 240, 240))
    # Standard mode
    proc_std, meta_std = ImagePreprocessor.process_pipeline(pil_img, mode="standard", upscale_factor=1.0)
    assert meta_std["mode"] == "standard"
    assert len(proc_std.shape) == 2

    # Grayscale only mode
    proc_gray, meta_gray = ImagePreprocessor.process_pipeline(pil_img, mode="grayscale_only", upscale_factor=1.0)
    assert meta_gray["mode"] == "grayscale_only"

    # None mode (raw pass-through)
    proc_none, meta_none = ImagePreprocessor.process_pipeline(pil_img, mode="none")
    assert meta_none["mode"] == "none"
    assert len(proc_none.shape) == 3
