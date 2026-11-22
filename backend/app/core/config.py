from pathlib import Path
from pydantic_settings import BaseSettings

# config.py is at: TuniVerse/backend/app/core/config.py
# .parent x4    → TuniVerse/  (project root where .env lives)
ENV_FILE = Path(__file__).resolve().parent.parent.parent.parent / ".env"


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ENVIRONMENT: str = "development"

    class Config:
        env_file = str(ENV_FILE)


settings = Settings()
