from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings.
    For now this only contains the database URL.
    You can later move this to an .env file.
    """

    # For first run, using SQLite is easiest.
    # Once Postgres is ready, change this to a Postgres URL.
    DATABASE_URL: str = "sqlite:///./gymbro.db"
    # Example Postgres URL:
    # DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/gymbro"

    class Config:
        env_file = ".env"


# This is what other modules import: `from .config import settings`
settings = Settings()
