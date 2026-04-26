from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Groq API (free)
    groq_api_key: str

    # App settings
    app_name: str = "Universal Data Understanding Agent"
    app_version: str = "1.0.0"
    debug: bool = False

    # Dataset limits
    max_file_size_mb: int = 50
    max_rows_before_sampling: int = 10_000
    sample_size: int = 5_000

    # Groq model — llama3 is free and very capable
    groq_model: str = "llama-3.1-8b-instant"
    groq_max_tokens: int = 2048

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()