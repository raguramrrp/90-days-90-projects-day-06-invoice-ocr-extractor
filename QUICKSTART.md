# Quickstart Guide: Automated Invoice Data Extraction System

Get the application up and running on Windows in under 2 minutes.

---

## Method 1: Automated Windows Setup (Recommended)

1. Double-click **`setup.bat`** (or execute from terminal):
   ```cmd
   setup.bat
   ```
   *This automatically checks Python, initializes `.venv`, installs all dependencies, copies `.env`, verifies Tesseract OCR, and seeds the sample database.*

2. Launch the Streamlit web dashboard:
   ```cmd
   run.bat
   ```
   *The application will launch and open in your default browser at `http://localhost:8501`.*

3. Execute the automated test suite:
   ```cmd
   test.bat
   ```

---

## Method 2: Manual Windows Setup

If you prefer to configure the environment manually via Command Prompt or PowerShell:

### 1. Prerequisites
- **Python 3.10+** (Tested on Python 3.12 64-bit).
- **Tesseract OCR**:
  - Install via PowerShell:
    ```cmd
    winget install UB-Mannheim.TesseractOCR --accept-source-agreements --accept-package-agreements
    ```
  - Standard install path: `C:\Program Files\Tesseract-OCR\tesseract.exe`.

### 2. Create and Activate Virtual Environment
```cmd
cd "D:\90 days\90-days-90-projects-day-06-invoice-ocr-extractor"
py -3.12 -m venv .venv
.venv\Scripts\activate
```

### 3. Install Dependencies
```cmd
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment
```cmd
copy .env.example .env
```

### 5. Generate Samples & Seed Database
```cmd
python scripts\generate_sample_invoices.py
python scripts\seed_database.py
```

### 6. Run Automated Tests
```cmd
pytest -v
```

### 7. Start the Web Dashboard
```cmd
streamlit run app.py
```
Open **`http://localhost:8501`**.
