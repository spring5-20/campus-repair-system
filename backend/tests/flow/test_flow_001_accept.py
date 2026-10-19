"""FLOW-001 接单属维修人员动作（BE2 轮次实现）。

S3 实现状态迁移接口后，学生调用 ACCEPT 返回 403；此骨架锁定该行为，
正式接单测试由 BE2 轮次补全。
"""


async def test_flow_001_student_cannot_accept(client):
    resp = await client.post(
        "/api/auth/login", json={"username": "student", "password": "123456"}
    )
    assert resp.status_code == 200
    headers = {"Authorization": f"Bearer {resp.json()['data']['token']}"}

    created = await client.post(
        "/api/tickets",
        headers=headers,
        json={
            "title": "接单权限测试",
            "description": "学生尝试接单应被拒绝",
            "category": "教学设备",
            "location": "实训楼 A-302",
        },
    )
    assert created.status_code == 200
    ticket_id = created.json()["data"]["id"]

    resp = await client.patch(
        f"/api/tickets/{ticket_id}/status",
        headers=headers,
        json={"action": "ACCEPT"},
    )
    assert resp.status_code == 403
    assert resp.json()["code"] == 403