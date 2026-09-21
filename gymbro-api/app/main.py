import logging
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

    # httpx logs every request URL at INFO. Credentials are sent in headers, not URLs, but a URL
    # can still carry a user's query text, and an INFO line per outbound call is noise.
    logging.getLogger("httpx").setLevel(logging.WARNING)

    # CORS: an explicit allow-list. The optional regex is unset by default -
    # see CORS_PREVIEW_ORIGIN_REGEX in config.py for why.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_origin_regex=settings.cors_preview_origin_regex,
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
