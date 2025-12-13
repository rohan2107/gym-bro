from fastapi import FastAPI

from .db import init_db
from .routers import health
from .routers import food_logs


def create_app() -> FastAPI:
    app = FastAPI(title="Gym Bro API")

    # Include routers
    app.include_router(health.router)
    app.include_router(food_logs.router)

    @app.on_event("startup")
    def on_startup():
        init_db()

    return app


app = create_app()
