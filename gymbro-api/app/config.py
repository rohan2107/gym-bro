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
    GOOGLE_REDIRECT_URI: str = ""
    JWT_SECRET_KEY: str = ""

    # External AI/nutrition services
    GOOGLE_VISION_API_KEY: str = ""
    USDA_API_KEY: str = ""

    FRONTEND_URL: str = "http://localhost:5173"

    # CORS. Local dev origins are always allowed; production origins are listed
    # explicitly. Vercel preview deployments are matched by a regex anchored to
    # this project's deployment-URL prefix rather than the whole vercel.app
    # namespace (which would make every site on vercel.app a credentialed
    # origin).
    CORS_ALLOWED_ORIGINS: str = "https://gym-bro-chi.vercel.app"
    CORS_PREVIEW_ORIGIN_REGEX: str = r"^https://gym-bro-[a-z0-9-]+\.vercel\.app$"

    ENVIRONMENT: str = "development"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

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
