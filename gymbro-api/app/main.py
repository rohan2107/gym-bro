from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import health, food_logs, daily_checkins, weight_entries, workouts, exercise_sets, auth
from .db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize database tables (safe for serverless)
    try:
        init_db()
    except Exception as e:
        # Log but don't crash - tables might already exist
        print(f"Warning: init_db failed (tables may already exist): {e}")
    yield
    # Shutdown: cleanup if needed


def create_app() -> FastAPI:
    app = FastAPI(
        title="Gym Bro API",
        lifespan=lifespan,
        root_path="/api",  # Vercel routes /api/* to this app
    )

    # CORS: Allow frontend from Vercel and local development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",  # Vite dev server
            "http://localhost:4173",  # Vite preview
        ],
        allow_origin_regex=r"https://.*\.vercel\.app",  # Vercel production & preview
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
