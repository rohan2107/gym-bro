from contextlib import asynccontextmanager
from fastapi import FastAPI

from .db import init_db
from .routers import health, food_logs, daily_checkins, weight_entries, workouts, exercise_sets


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    yield
    # Shutdown (nothing needed yet)


def create_app() -> FastAPI:
    app = FastAPI(
        title="Gym Bro API",
        lifespan=lifespan,
    )

    # Include routers
    app.include_router(health.router)
    app.include_router(food_logs.router)
    app.include_router(daily_checkins.router)
    app.include_router(weight_entries.router)
    app.include_router(workouts.router)
    app.include_router(exercise_sets.router)

    return app


app = create_app()
