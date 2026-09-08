"""
Convenience entrypoint allowing uvicorn to run directly from either
the stage root directory or the backend/ directory.
"""
import sys
from pathlib import Path

STAGE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = STAGE_DIR / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(STAGE_DIR) not in sys.path:
    sys.path.insert(0, str(STAGE_DIR))

from backend.main import app  # noqa: F401

__all__ = ["app"]
