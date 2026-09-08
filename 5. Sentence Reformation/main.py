"""
Convenience entrypoint allowing uvicorn to run directly from either
the stage root directory or the backend/ directory.
"""
import sys
from pathlib import Path

# Add backend directory to sys.path so app packages resolve cleanly
BACKEND_DIR = Path(__file__).resolve().parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from main import app  # noqa: F401
