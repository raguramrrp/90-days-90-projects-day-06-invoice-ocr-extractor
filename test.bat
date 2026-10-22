@echo off
setlocal

echo =====================================================================
echo  Running Automated Test Suite (Invoice OCR Extractor)
echo =====================================================================

if not exist ".venv\Scripts\pytest.exe" (
    echo [ERROR] Virtual environment not found. Please run setup.bat first.
    pause
    exit /b 1
)

.venv\Scripts\pytest.exe -v --tb=short
set TEST_EXIT_CODE=%ERRORLEVEL%

echo =====================================================================
if %TEST_EXIT_CODE% equ 0 (
    echo [PASS] All automated tests passed successfully!
) else (
    echo [FAIL] One or more tests failed. Review output above.
)
echo =====================================================================

exit /b %TEST_EXIT_CODE%
