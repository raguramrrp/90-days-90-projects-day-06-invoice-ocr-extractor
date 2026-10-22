# Troubleshooting & Common Issues Guide

This guide covers common issues, root causes, and resolutions for the Invoice OCR Extractor on Windows systems.

---

## 1. Tesseract OCR Binary Issues

### Error: `pytesseract.pytesseract.TesseractNotFoundError: tesseract is not installed or it's not in your PATH`
- **Cause**: Tesseract OCR engine binary (`tesseract.exe`) is not installed on the host machine or its path is not registered.
- **Resolution**:
  1. Install Tesseract on Windows using winget:
     ```cmd
     winget install UB-Mannheim.TesseractOCR --accept-source-agreements --accept-package-agreements
     ```
  2. Or download the installer directly from the official [UB-Mannheim Tesseract Wiki](https://github.com/UB-Mannheim/tesseract/wiki).
  3. Default install location is `C:\Program Files\Tesseract-OCR\tesseract.exe`.
  4. If installed to a non-standard directory, open `.env` and set:
     ```env
     TESSERACT_CMD=D:\CustomPath\Tesseract-OCR\tesseract.exe
     ```
  5. Run diagnostic verification:
     ```cmd
     .venv\Scripts\python.exe scripts\verify_tesseract.py
     ```

---

## 2. Document Processing & Image Quality

### Issue: Low OCR Confidence or Garbled Text on Photographs
- **Cause**: Uneven lighting, shadows, camera perspective tilt, or low camera resolution.
- **Resolution**:
  - In the Streamlit sidebar, change **Thresholding Mode** from `standard` to `adaptive`. Adaptive Gaussian thresholding calculates local pixel thresholds, eliminating background shadow gradients.
  - Ensure **Auto-Deskew** is checked.
  - Increase the **High-DPI Upscale Factor** to $2.0\times$ or $2.5\times$ to enlarge small numbers.

### Issue: Product Description and Price Split onto Separate Lines
- **Cause**: Multi-column text layouts read in `PSM 3` (automatic page segmentation).
- **Resolution**: The system defaults to `PSM 4` ("single column of variable sizes"), which forces line-by-line horizontal reading across column boundaries.

---

## 3. Financial Discrepancies

### Warning: `Total mismatch: Extracted total differs from calculated balance`
- **Cause**:
  1. The invoice may contain a line item discount or tax calculation not parsed by the regular expressions.
  2. OCR misread a decimal point as a comma or omitted a digit.
- **Resolution**:
  - Navigate to **Tab 3: Edit & Validate**.
  - Review the extracted numbers against the visual document preview in Tab 1.
  - Adjust the values directly in the form, edit the line items data grid, and click **"Save Validated Invoice to Database"**.

---

## 4. Environment & Python Setup Issues

### Error: `python.exe: No module named venv` or Python Version Conflict
- **Cause**: Python was installed without standard virtual environment tools or a pre-release version was used.
- **Resolution**:
  - The project is fully tested on **Python 3.12 (64-bit)**.
  - Run setup using the Windows Python launcher:
    ```cmd
    py -3.12 -m venv .venv
    .venv\Scripts\python.exe -m pip install -r requirements.txt
    ```

### Error: Streamlit Port 8501 Already in Use
- **Cause**: Another local development server is listening on port 8501.
- **Resolution**:
  - Launch Streamlit on an alternate port:
    ```cmd
    .venv\Scripts\streamlit.exe run app.py --server.port=8502
    ```
