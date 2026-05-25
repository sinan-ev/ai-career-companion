from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """
    Application configuration settings loaded from environment variables.

    Attributes:
        groq_api_key (str): API key for the Groq service.
        app_name (str): The name of the application.
        app_version (str): The version of the application.
        debug (bool): Flag to enable or disable debug mode.
        max_file_size_mb (int): Maximum allowed file size for upload in megabytes.
        max_rows_before_sampling (int): Threshold of rows before sampling is triggered.
        sample_size (int): Size of the sample to extract if threshold is exceeded.
        groq_model (str): Name of the Groq model to use.
        groq_max_tokens (int): Maximum tokens for Groq model generation.
        storage_backend (str): Storage backend to use ('local' or 'gcs').
        gcs_bucket_name (str): GCS bucket name for artifact storage (required when storage_backend='gcs').
    """

    # pydantic-settings v2 config — extra="ignore" silences GCP-injected
    # env vars like PORT, K_SERVICE, etc. that are not declared fields.
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

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

    # Storage config (set via env vars on Cloud Run)
    storage_backend: str = "local"
    gcs_bucket_name: str = ""


@lru_cache()
def get_settings() -> Settings:
    """
    Retrieve cached application settings.
    
    Returns:
        Settings: The application settings instance.
    """
    return Settings()
