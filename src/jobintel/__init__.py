"""JobIntel - AI-powered job scraping, resume matching, and tailored resume generation."""

from pathlib import Path

__version__ = "1.0.0"
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
TEMPLATES_DIR = PROJECT_ROOT / "templates"
