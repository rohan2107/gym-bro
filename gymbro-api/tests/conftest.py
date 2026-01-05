import sys
from pathlib import Path

# Ensure the app package is importable when running tests from project root
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
