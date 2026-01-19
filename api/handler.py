"""Vercel serverless handler for FastAPI app."""
import sys
from pathlib import Path

# Add gymbro-api to Python path so we can import from app
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root / "gymbro-api"))

from mangum import Mangum
from app.main import app

# Vercel calls this function for every request
handler = Mangum(app)
