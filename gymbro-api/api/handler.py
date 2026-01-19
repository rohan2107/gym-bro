"""Vercel serverless handler for FastAPI app."""
from mangum import Mangum
from app.main import app

# Vercel calls this function for every request
handler = Mangum(app)
