from locust import task, HttpUser, run_single_user, between
import random


class RateLimiter(HttpUser):
    host = "http://127.0.0.1:8001"
    wait_time = between(0.1, 0.5)


    def on_start(self):
        self.client.headers = {"UserId": str(random.randint(1, 100000))}

    @task
    def health_check(self):
        self.client.get("/")

