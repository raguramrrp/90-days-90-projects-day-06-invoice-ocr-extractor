@echo off
setlocal

echo =====================================================================
echo  Starting Invoice OCR Extractor Application...
echo =====================================================================

if not exist ".venv\Scripts\streamlit.exe" (
    echo [ERROR] Virtual environment not found. Please run setup.bat first.
    pause
    exit /b 1
)

echo [INFO] Activating virtual environment and starting Streamlit server...
echo [INFO] Web Dashboard URL: http://localhost:8501
echo [INFO] Press Ctrl+C in this terminal window to stop the application.
echo =====================================================================

.venv\Scripts\streamlit.exe run app.py --server.port=8501 --server.headless=false

if %ERRORLEVEL% neq 0 (
    echo [ERROR] Application failed to start or crashed.
    pause
)
