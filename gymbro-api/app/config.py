from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings.

    Every externally-configured value the app reads should be declared here, so
    the environment contract lives in exactly one place.
    """

    DATABASE_URL: str = "sqlite:///./gymbro.db"

    # Auth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    JWT_SECRET_KEY: str = ""

    # External AI/nutrition services
    # Which provider recognises foods in photos. An unknown value fails at startup, not at
    # the first photo.
    FOOD_RECOGNITION_PROVIDER: Literal["gemini", "vision"] = "gemini"
    GEMINI_API_KEY: str = ""
    # Model ids are pinned, never a `-latest` alias: an alias changes under us and makes
    # measured accuracy unrepeatable. The fallback is tried when the primary is rate
    # limited or erroring; it has its own quota.
    GEMINI_MODEL: str = "gemini-3.5-flash-lite"
    GEMINI_FALLBACK_MODEL: str = "gemini-3.1-flash-lite"
    GOOGLE_VISION_API_KEY: str = ""
    USDA_API_KEY: str = ""

    FRONTEND_URL: str = "http://localhost:5173"

    # CORS. Local dev origins are always allowed; production origins are listed
    # explicitly.
    CORS_ALLOWED_ORIGINS: str = "https://gym-bro-chi.vercel.app"

    # Optional regex for additional allowed origins. Empty by default, and
    # deliberately so: on Vercel the frontend and this API are served from the
    # same deployment, so browser requests to /api/* are same-origin and never
    # consult CORS. A pattern like "^https://gym-bro-[a-z0-9-]+\.vercel\.app$"
    # looks project-scoped but is not - anyone can deploy a project named
    # gym-bro-anything and would become an allowed credentialed origin. If
    # cross-origin previews are ever needed, set this to a pattern that includes
    # the team slug, e.g. "^https://gym-bro-[a-z0-9-]+-myteam\.vercel\.app$".
    CORS_PREVIEW_ORIGIN_REGEX: str = ""

    # Deliberately defaults to "production". This value gates the X-User-Id dev
    # auth header (see app/deps.py), which lets a caller act as any user. The
    # previous default of "development" meant a deployment that never set this
    # variable - as Vercel never did - accepted that header from anyone.
    # Set ENVIRONMENT=development in a local .env to opt in.
    ENVIRONMENT: str = "production"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_preview_origin_regex(self) -> str | None:
        """The preview-origin regex, or None when unset.

        Starlette compiles whatever it is given, so an empty string must become
        None rather than being passed through as a pattern.
        """
        return self.CORS_PREVIEW_ORIGIN_REGEX or None

    @property
    def cors_allowed_origins(self) -> list[str]:
        """Explicit allowed origins: local dev plus any configured production origins."""
        local = [
            "http://localhost:5173",  # Vite dev server
            "http://localhost:4173",  # Vite preview
        ]
        configured = [
            origin.strip()
            for origin in self.CORS_ALLOWED_ORIGINS.split(",")
            if origin.strip()
        ]
        # Preserve order, drop duplicates.
        return list(dict.fromkeys(local + configured))


settings = Settings()
