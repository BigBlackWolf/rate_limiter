import time
from dataclasses import dataclass
from typing import Dict, Optional

import uvicorn
from fastapi import FastAPI, Response, status
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

app = FastAPI()


@dataclass
class BucketRecord:
    last_update: float
    tokens: int


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RATE_LIMITER_", case_sensitive=False)

    bucket: Dict[int | str, BucketRecord] = {}

    limit: Optional[int] = Field(default=None)
    number_of_tokens: int = Field(default=3)
    window: int = Field(default=10)


@app.get("/health-check")
def health_check(response: Response):
    response.status_code = status.HTTP_200_OK
    return {"status": "OK"}


@app.get("/{user_id}")
def check_rate(user_id: int | str, response: Response):
    fill(user_id)
    if settings.bucket[user_id].tokens > 0:
        settings.bucket[user_id].tokens -= 1
        response.status_code = status.HTTP_200_OK
        return {"status": "OK"}
    response.status_code = status.HTTP_429_TOO_MANY_REQUESTS
    return {"status": "ERROR"}


def fill(user_id: int | str):
    current_time = time.time()
    if user_id not in settings.bucket:
        settings.bucket[user_id] = BucketRecord(current_time, settings.number_of_tokens)
        return

    user_record = settings.bucket[user_id]
    time_passed = int(current_time - user_record.last_update)
    if time_passed > settings.window:
        new_value = settings.number_of_tokens
        user_record.last_update = time.time()

        if settings.limit:
            mulitplier = int(time_passed // settings.window)
            new_value = min(
                user_record.tokens + settings.number_of_tokens * mulitplier,
                settings.limit,
            )

            # Deducting time, which is above window time to keep window follow static periods
            # e.g. window = 3, time_passed = 4 secs -> deducting 1 second and set is an update time
            window_on_top = time_passed % settings.window
            user_record.last_update = time.time() - window_on_top
        user_record.tokens = new_value


if __name__ == "__main__":
    settings = Settings()
    print(settings)
    uvicorn.run(app)
