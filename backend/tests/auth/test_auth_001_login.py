import pytest


@pytest.mark.parametrize(
    ("username", "display_name", "role"),
    [
        ("student", "学生用户", "student"),
        ("tech", "维修人员", "tech"),
        ("admin", "系统管理员", "admin"),
    ],
)
async def test_auth_001_login_success(client, username, display_name, role):
    resp = await client.post(
        "/api/auth/login", json={"username": username, "password": "123456"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["token"]
    assert body["data"]["user"]["displayName"] == display_name
    assert body["data"]["user"]["role"] == role


async def test_auth_001_login_wrong_password(client):
    resp = await client.post(
        "/api/auth/login", json={"username": "student", "password": "wrong"}
    )
    assert resp.status_code == 401
    assert resp.json()["code"] == 401


async def test_auth_001_login_unknown_account(client):
    resp = await client.post(
        "/api/auth/login", json={"username": "nobody", "password": "123456"}
    )
    assert resp.status_code == 401
    assert resp.json()["code"] == 401