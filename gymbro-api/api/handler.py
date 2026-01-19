"""Vercel serverless handler for FastAPI app."""
from vercel_asgi import asgi_handler
from app.main import app

# Vercel calls this function for every request
handler = asgi_handler(app)
