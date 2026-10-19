"""USER-001 用户列表测试（FLOW-002 指派下拉数据源）。

覆盖：admin 可见全部用户（不含密码字段）、role=tech 筛选出维修人员、
非管理员 403、非法 role 422、未登录 401。
"""

from tests.admin.helpers import auth_headers


async def test_users_001_requires_login(seeded_client):
    client, _ = seeded_client
    resp = await client.get("/api/users")
    assert resp.status_code == 401
    assert resp.json()["code"] == 401


async def test_users_001_admin_lists_all_users(seeded_client):
    client, _ = seeded_client
    headers = await auth_headers(client, "admin")
    resp = await client.get("/api/users", headers=headers)
    assert resp.status_code == 200
    users = resp.json()["data"]
    assert {u["username"] for u in users} == {
        "student",
        "student2",
        "tech",
        "tech2",
        "admin",
    }
    # 只暴露下拉框需要的字段，不含密码
    assert all(set(u) == {"id", "username", "displayName", "role"} for u in users)


async def test_users_001_role_filter_tech(seeded_client):
    client, _ = seeded_client
    headers = await auth_headers(client, "admin")
    resp = await client.get("/api/users", headers=headers, params={"role": "tech"})
    assert resp.status_code == 200
    users = resp.json()["data"]
    assert {u["username"] for u in users} == {"tech", "tech2"}
    assert all(u["role"] == "tech" for u in users)


async def test_users_001_non_admin_returns_403(seeded_client):
    client, _ = seeded_client
    for username in ("student", "tech"):
        headers = await auth_headers(client, username)
        resp = await client.get("/api/users", headers=headers)
        assert resp.status_code == 403
        assert resp.json()["code"] == 403


async def test_users_001_invalid_role_returns_422(seeded_client):
    client, _ = seeded_client
    headers = await auth_headers(client, "admin")
    resp = await client.get("/api/users", headers=headers, params={"role": "other"})
    assert resp.status_code == 422
    assert resp.json()["code"] == 422
