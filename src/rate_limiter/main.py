import logging
import time
from typing import Dict

import uvicorn
from fastapi import FastAPI, HTTPException, Request, Response, status, Depends

from rate_limiter.settings import settings
from rate_limiter.storage import get_storage, DB

logging.basicConfig(level=logging.INFO)

logging.info(settings)
app = FastAPI()


@app.get("/health-check")
def health_check(response: Response):
    response.status_code = status.HTTP_200_OK
    return {"status": "OK"}


@app.get("/")
def check_rate(response: Response, request: Request, db = Depends(get_storage)):
    user_id = request.headers.get("userId", "")
    if not user_id:
        raise HTTPException(
            detail="User can't be identified", status_code=status.HTTP_400_BAD_REQUEST
        )

    refill(user_id, db)

    if db[user_id].tokens > 0:
        db.dec(user_id)
        response.status_code = status.HTTP_200_OK
        return {"status": "OK"}

    raise HTTPException(
        detail="Too many requests", status_code=status.HTTP_429_TOO_MANY_REQUESTS
    )


def refill(user_id: str, db: DB) -> None:
    current_time = time.time()
    if user_id not in db:
        db[user_id] = current_time, settings.number_of_tokens
        return

    user_record = db[user_id]
    time_passed = int(current_time - user_record.last_update)
    if time_passed >= settings.window:
        new_value = settings.number_of_tokens
        new_time = time.time()

        if settings.limit:
            mulitplier = int(time_passed // settings.window)
            new_value = min(
                user_record.tokens + settings.number_of_tokens * mulitplier,
                settings.limit,
            )

            # Deducting time, which is above window time to keep window follow static periods
            # e.g. window = 3, time_passed = 4 secs -> deducting 1 second and set is an update time
            window_on_top = time_passed % settings.window
            new_time = time.time() - window_on_top

        db[user_id] = new_time, new_value