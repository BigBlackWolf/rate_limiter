import logging
import time
from typing import Dict

import uvicorn
from fastapi import FastAPI, Request, Response, status

from rate_limiter.settings import BucketRecord, Settings

logging.basicConfig(level=logging.INFO)
settings = Settings()

logging.info(settings)
app = FastAPI()

BUCKET: Dict[int | str, BucketRecord] = {}


@app.get("/health-check")
def health_check(response: Response):
    response.status_code = status.HTTP_200_OK
    return {"status": "OK"}


@app.get("/")
def check_rate(response: Response, request: Request):
    if not request.client or not request.client.host:
        response.status_code = status.HTTP_429_TOO_MANY_REQUESTS
        return {"status": "ERROR"}

    user_id = request.client.host
    fill(user_id)
    if BUCKET[user_id].tokens > 0:
        BUCKET[user_id].tokens -= 1
        response.status_code = status.HTTP_200_OK
        return {"status": "OK"}
    response.status_code = status.HTTP_429_TOO_MANY_REQUESTS
    return {"status": "ERROR"}


def fill(user_id: int | str):
    current_time = time.time()
    if user_id not in BUCKET:
        BUCKET[user_id] = BucketRecord(current_time, settings.number_of_tokens)
        return

    user_record = BUCKET[user_id]
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
