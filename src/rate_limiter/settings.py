from dataclasses import dataclass
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="RATE_LIMITER_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        )

    limit: Optional[int] = Field(default=None)
    number_of_tokens: int = Field(default=3)
    window: int = Field(default=10)
    redis_host: Optional[str] = Field(default=None)
    redis_port: Optional[int] = Field(default=None)


settings = Settings()