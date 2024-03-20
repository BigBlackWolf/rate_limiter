import logging
import time
from typing import Dict

import uvicorn
from fastapi import FastAPI, HTTPException, Request, Response, status, Depends

from rate_limiter.settings import settings
from rate_limiter.storage import get_storage, DB, refill

logging.basicConfig(level=logging.INFO)

logging.info(settings)
app = FastAPI()


@app.get("/health-check")
def health_check(response: Response):
    response.status_code = status.HTTP_200_OK
    return {"status": "OK"}


@app.get("/")
def check_rate(response: Response, request: Request, db: DB = Depends(get_storage)):
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
