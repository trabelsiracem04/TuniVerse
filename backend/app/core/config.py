from pathlib import Path
from pydantic_settings import BaseSettings

BACKEND_ENV = Path(__file__).resolve().parent.parent.parent / ".env"
ROOT_ENV = Path(__file__).resolve().parent.parent.parent.parent / ".env"
ENV_FILE = BACKEND_ENV if BACKEND_ENV.exists() else ROOT_ENV


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ENVIRONMENT: str = "development"

    class Config:
        env_file = str(ENV_FILE)


settings = Settings()
