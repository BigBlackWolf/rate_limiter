from typing import Dict, Tuple
import redis
from dataclasses import dataclass
import time

import os
from rate_limiter.settings import settings
import json


@dataclass
class BucketRecord:
    last_update: float
    tokens: int

    def serialize(self):
        output = {"tokens": self.tokens, "last_update": self.last_update}
        return json.dumps(output)


BUCKET: Dict[int | str, BucketRecord] = {}


class DB:
    def __init__(self, client: None | redis.Redis = None):
        if client is None:
            client = BUCKET
        self.client = client
    
    def __getitem__(self, item: str) -> BucketRecord:
        value = self.client.get(item)
        if not isinstance(self.client, dict):
            deserialized = json.loads(value)
            value = BucketRecord(**deserialized)
        return value
    
    def __setitem__(self, key: str, value: Tuple[float, int]) -> None:
        new_value = BucketRecord(*value)
        if isinstance(self.client, dict):
            self.client[key] = new_value
        else:
            self.client.set(key, new_value.serialize())
    
    def __contains__(self, item: str) -> bool:
        if isinstance(self.client, dict):
            value = item in self.client
        else:
            value = self.client.exists(item)
        return value
    
    def dec(self, user_id: str) -> None:
        if isinstance(self.client, dict):
            self.client[user_id].tokens -= 1
        else:
            value = self[user_id]
            value.tokens -= 1
            self[user_id] = value.last_update, value.tokens


def get_storage() -> DB:
    client = None
    if settings.redis_host:
        client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
        )
    return DB(client)


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
