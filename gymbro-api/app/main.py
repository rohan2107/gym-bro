from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import health, food_logs, daily_checkins, weight_entries, workouts, exercise_sets, auth
from .config import settings
from .db import check_db_connection


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: verify the database is reachable. Schema changes are applied by
    # Alembic, not here - see check_db_connection().
    check_db_connection()
    yield
    # Shutdown: cleanup if needed


def create_app() -> FastAPI:
    app = FastAPI(
        title="Gym Bro API",
        lifespan=lifespan,
        root_path="/api",  # Vercel routes /api/* to this app
    )

    # CORS: explicit origins for local dev and production, plus a regex scoped
    # to this project's own Vercel preview URLs.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_origin_regex=settings.CORS_PREVIEW_ORIGIN_REGEX,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(food_logs.router)
    app.include_router(daily_checkins.router)
    app.include_router(weight_entries.router)
    app.include_router(workouts.router)
    app.include_router(exercise_sets.router)

    return app


app = create_app()
