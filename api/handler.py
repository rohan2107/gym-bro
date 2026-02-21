"""Vercel serverless handler for FastAPI app."""
import sys
from pathlib import Path

# Add gymbro-api to Python path so we can import from app
repo_root = Path(__file__).parent.parent
gymbro_api_path = repo_root / "gymbro-api"
sys.path.insert(0, str(gymbro_api_path))

# Import and create the FastAPI app
from app.main import create_app

# Create the app instance for Vercel
app = create_app()

