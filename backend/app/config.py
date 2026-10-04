from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    secret_key: str
    ai_api_key: str = ""
    ai_model: str = "claude-sonnet-5-5"
    ai_api_url: str = "https://api.anthropic.com/v1/messages"
    cors_origins: str = "http://localhost:5173"
    access_token_expire_minutes: int = 720
    jwt_algorithm: str = "HS256"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()