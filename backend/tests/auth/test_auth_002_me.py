from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import get_settings


async def _login(client, username="student", password="123456"):
    resp = await client.post(
        "/api/auth/login", json={"username": username, "password": password}
    )
    assert resp.status_code == 200
    return resp.json()["data"]["token"]


async def test_auth_002_me_restores_user(client):
    token = await _login(client)
    resp = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["username"] == "student"
    assert body["data"]["role"] == "student"


async def test_auth_002_me_works_for_tech(client):
    token = await _login(client, username="tech")
    resp = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["data"]["role"] == "tech"


async def test_auth_002_me_invalid_token(client):
    resp = await client.get("/api/auth/me", headers={"Authorization": "Bearer bad-token"})
    assert resp.status_code == 401
    assert resp.json()["code"] == 401


async def test_auth_002_me_missing_header(client):
    resp = await client.get("/api/auth/me")
    assert resp.status_code == 401
    assert resp.json()["code"] == 401


async def test_auth_002_me_expired_token(client):
    settings = get_settings()
    expired = jwt.encode(
        {
            "sub": "1",
            "role": "student",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        },
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    resp = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired}"})
    assert resp.status_code == 401
    assert resp.json()["code"] == 401


async def test_auth_002_me_unknown_user_token(client):
    settings = get_settings()
    ghost = jwt.encode(
        {
            "sub": "999999",
            "role": "student",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        },
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    resp = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {ghost}"})
    assert resp.status_code == 401
    assert resp.json()["code"] == 401