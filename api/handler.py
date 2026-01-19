"""Vercel serverless handler for FastAPI app."""
import sys
from pathlib import Path

# Add gymbro-api to Python path so we can import from app
repo_root = Path(__file__).parent.parent
gymbro_api_path = repo_root / "gymbro-api"
sys.path.insert(0, str(gymbro_api_path))

# Import the FastAPI app directly - Vercel supports it natively
from app.main import app

# Vercel uses the 'app' variable directly (no adapter needed)
