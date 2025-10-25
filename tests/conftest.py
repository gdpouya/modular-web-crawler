"""Configure test environment."""
import os
import sys
from pathlib import Path

# Add src directory to Python path
root = Path(__file__).parent.parent
src_path = str(root / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)