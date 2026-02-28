from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    spreadsheet_id: str
    google_application_credentials: str

    model_config = {"env_file": ".env"}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
