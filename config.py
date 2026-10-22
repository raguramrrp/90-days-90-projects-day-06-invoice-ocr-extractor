"""Application Configuration and System Path Management.

Handles environment loading, Tesseract OCR binary auto-discovery,
database paths, and runtime settings for the Invoice OCR Extractor.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent

# Load .env file
load_dotenv(BASE_DIR / ".env")

# App Metadata
APP_NAME = os.getenv("APP_NAME", "Automated Invoice Data Extraction & Structuring System")
APP_ENV = os.getenv("APP_ENV", "development")
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

# Database Configuration
DEFAULT_DB_PATH = BASE_DIR / "data" / "invoices.db"
DATABASE_PATH = Path(os.getenv("DATABASE_PATH", str(DEFAULT_DB_PATH)))
if not DATABASE_PATH.is_absolute():
    DATABASE_PATH = BASE_DIR / DATABASE_PATH
DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

# Extraction & Processing Defaults
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.60"))
ALLOWED_EXTENSIONS = [
    ext.strip().lower()
    for ext in os.getenv("ALLOWED_EXTENSIONS", "png,jpg,jpeg,tiff,pdf").split(",")
]
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "10"))

# Known Tesseract Binary Paths on Windows and POSIX systems
COMMON_TESSERACT_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
    os.path.expandvars(r"%LOCALAPPDATA%\Tesseract-OCR\tesseract.exe"),
    "/usr/bin/tesseract",
    "/usr/local/bin/tesseract",
    "/opt/homebrew/bin/tesseract",
]


def resolve_tesseract_path() -> str | None:
    """Auto-detect Tesseract OCR binary across env, PATH, and standard directories."""
    # 1. Explicit env configuration
    env_path = os.getenv("TESSERACT_CMD")
    if env_path and Path(env_path).is_file():
        return env_path

    # 2. Check system PATH
    which_path = shutil.which("tesseract")
    if which_path and Path(which_path).is_file():
        return which_path

    # 3. Check common Windows / POSIX install paths
    for path_str in COMMON_TESSERACT_PATHS:
        candidate = Path(path_str)
        if candidate.is_file():
            return str(candidate)

    return None


# Initialize pytesseract configuration upon import
TESSERACT_EXECUTABLE = resolve_tesseract_path()
if TESSERACT_EXECUTABLE:
    try:
        import pytesseract
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_EXECUTABLE
    except ImportError:
        pass


def get_system_diagnostics() -> Dict[str, Any]:
    """Return runtime diagnostic information for UI and verification scripts."""
    ocr_available = False
    ocr_version = "Not Detected"

    if TESSERACT_EXECUTABLE:
        try:
            import pytesseract
            version_str = pytesseract.get_tesseract_version()
            ocr_version = str(version_str)
            ocr_available = True
        except Exception as e:
            ocr_version = f"Error: {e}"

    return {
        "app_name": APP_NAME,
        "base_dir": str(BASE_DIR),
        "database_path": str(DATABASE_PATH),
        "tesseract_executable": TESSERACT_EXECUTABLE,
        "ocr_available": ocr_available,
        "ocr_version": ocr_version,
        "confidence_threshold": CONFIDENCE_THRESHOLD,
        "allowed_extensions": ALLOWED_EXTENSIONS,
        "max_file_size_mb": MAX_FILE_SIZE_MB,
    }
