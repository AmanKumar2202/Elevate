from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Default to SQLite for local dev. Override with a full PostgreSQL URL in .env
    # for production (or use docker-compose which sets DATABASE_URL automatically).
    DATABASE_URL: str = "sqlite:///./performance_feedback.db"
    SECRET_KEY: str = "change-me-in-production-use-a-long-random-string-at-least-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
