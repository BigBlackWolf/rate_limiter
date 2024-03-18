import os
from typing import Generator

import trio
import httpx
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from rate_limiter.main import app, BUCKET, settings
from rate_limiter.settings import Settings


@pytest.fixture(scope="function")
async def test_client():
    transport = httpx.ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    BUCKET.clear()


@pytest.fixture
def too_many_requests():
    return {"detail": "Too many requests"}


@pytest.fixture
def user_not_set():
    return {"detail": "User can't be identified"}


@pytest.mark.anyio
async def test_health_check():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health-check")
    assert response.status_code == 200
    assert response.json() == {"status": "OK"}


@pytest.mark.anyio
async def test_rate_no_ip(user_not_set):
    transport = httpx.ASGITransport(app=app, client=("", 123))
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/")
    assert response.status_code == 400
    assert response.json() == user_not_set


@pytest.mark.anyio
async def test_rate_single(test_client):
    headers = {"userId": "1"}
    response = await test_client.get("/", headers=headers)
    assert response.status_code == 200
    assert response.json() == {"status": "OK"}


@pytest.mark.anyio
async def test_rate_multiple_no_limit(test_client, too_many_requests):
    max_attempts = 3
    settings.limit = 0
    settings.number_of_tokens = max_attempts
    settings.window = 5

    headers = {"userId": "1"}

    for _ in range(max_attempts):
        response = await test_client.get("/", headers=headers)
        assert response.status_code == 200
        assert response.json() == {"status": "OK"}

    response = await test_client.get("/", headers=headers)
    assert response.status_code == 429
    assert response.json() == too_many_requests


@pytest.mark.anyio
async def test_rate_multiple_no_limit_window(test_client, too_many_requests):
    max_attempts = 3
    window = 1

    settings.limit = 0
    settings.number_of_tokens = max_attempts
    settings.window = window

    headers = {"userId": "1"}

    for _ in range(max_attempts):
        response = await test_client.get("/", headers=headers)
        assert response.status_code == 200
        assert response.json() == {"status": "OK"}

    response = await test_client.get("/", headers=headers)
    assert response.status_code == 429
    assert response.json() == too_many_requests

    # Checking that window refilled tokens
    await trio.sleep(window)

    for _ in range(max_attempts):
        response = await test_client.get("/", headers=headers)
        assert response.status_code == 200
        assert response.json() == {"status": "OK"}
    
    response = await test_client.get("/", headers=headers)
    assert response.status_code == 429
    assert response.json() == too_many_requests


@pytest.mark.anyio
async def test_rate_multiple_limit(test_client, too_many_requests):
    max_attempts = 3
    window = 1
    limit = max_attempts * (window * 2)

    settings.limit = limit
    settings.number_of_tokens = max_attempts
    settings.window = window

    headers = {"userId": "1"}

    for _ in range(max_attempts):
        response = await test_client.get("/", headers=headers)
        assert response.status_code == 200
        assert response.json() == {"status": "OK"}

    response = await test_client.get("/", headers=headers)
    assert response.status_code == 429
    assert response.json() == too_many_requests

    # Checking that window refilled tokens, but not more then set limit
    await trio.sleep(window * (2 + 1))

    for _ in range(limit):
        response = await test_client.get("/", headers=headers)
        assert response.status_code == 200
        assert response.json() == {"status": "OK"}
    
    response = await test_client.get("/", headers=headers)
    assert response.status_code == 429
    assert response.json() == too_many_requests