from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import health, food_logs, daily_checkins, weight_entries, workouts, exercise_sets


def create_app() -> FastAPI:
    app = FastAPI(
        title="Gym Bro API",
    )

    # CORS: Allow frontend from Vercel and local development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",  # Vite dev server
            "http://localhost:4173",  # Vite preview
            "https://*.vercel.app",   # Vercel production & preview
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
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
