"""FLOW-004 学生取消/验收关闭测试（S3，成员 C）。

覆盖：鉴权 401、不存在/他人工单 404、PENDING→CANCELLED（AC-09）、
RESOLVED→CLOSED（AC-08）、接单后不能取消 409、错误状态迁移 409、
非学生动作（ACCEPT/RESOLVE）403、非法 action 422。
"""

import pytest

from tests.interaction.helpers import auth_headers, make_ticket, user_id


async def _create_owned_ticket(client, Session, *, status: str) -> int:
    """由 student 直接插入一张指定状态的工单，返回 id。"""
    student_id = await user_id(Session, "student")
    async with Session() as session:
        ticket = make_ticket(student_id, ticket_no="REP-0001", status=status)
        session.add(ticket)
        await session.commit()
        await session.refresh(ticket)
        return ticket.id


async def test_flow_004_requires_login(seeded_client):
    client, _ = seeded_client
    resp = await client.patch("/api/tickets/1/status", json={"action": "CANCEL"})
    assert resp.status_code == 401
    assert resp.json()["code"] == 401


async def test_flow_004_not_found_returns_404(seeded_client):
    client, _ = seeded_client
    headers = await auth_headers(client)
    resp = await client.patch(
        "/api/tickets/999/status", headers=headers, json={"action": "CANCEL"}
    )
    assert resp.status_code == 404


async def test_flow_004_other_students_ticket_is_404(seeded_client):
    client, Session = seeded_client
    other_id = await user_id(Session, "student2")
    async with Session() as session:
        ticket = make_ticket(other_id, ticket_no="REP-0001", status="PENDING")
        session.add(ticket)
        await session.commit()
        await session.refresh(ticket)
    headers = await auth_headers(client)
    resp = await client.patch(
        f"/api/tickets/{ticket.id}/status", headers=headers, json={"action": "CANCEL"}
    )
    assert resp.status_code == 404


async def test_flow_004_student_cancels_pending(seeded_client):
    """AC-09：PENDING→CANCELLED，写 CANCEL 日志。"""
    client, Session = seeded_client
    headers = await auth_headers(client)
    ticket_id = await _create_owned_ticket(client, Session, status="PENDING")

    resp = await client.patch(
        f"/api/tickets/{ticket_id}/status", headers=headers, json={"action": "CANCEL"}
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["id"] == ticket_id
    assert data["status"] == "CANCELLED"

    logs = (
        await client.get(f"/api/tickets/{ticket_id}/logs", headers=headers)
    ).json()["data"]
    assert logs[-1]["action"] == "CANCEL"
    assert logs[-1]["fromStatus"] == "PENDING"
    assert logs[-1]["toStatus"] == "CANCELLED"
    assert logs[-1]["detail"] == "学生取消工单"


async def test_flow_004_cancel_processing_returns_409(seeded_client):
    """AC-09：接单后（PROCESSING）学生不能取消，返回 409。"""
    client, Session = seeded_client
    headers = await auth_headers(client)
    ticket_id = await _create_owned_ticket(client, Session, status="PROCESSING")

    resp = await client.patch(
        f"/api/tickets/{ticket_id}/status", headers=headers, json={"action": "CANCEL"}
    )
    assert resp.status_code == 409
    assert resp.json()["code"] == 409

    # 状态未变
    detail = (
        await client.get(f"/api/tickets/{ticket_id}", headers=headers)
    ).json()["data"]
    assert detail["status"] == "PROCESSING"


async def test_flow_004_student_closes_resolved(seeded_client):
    """AC-08：RESOLVED→CLOSED，写 CLOSE 日志。"""
    client, Session = seeded_client
    headers = await auth_headers(client)
    ticket_id = await _create_owned_ticket(client, Session, status="RESOLVED")

    resp = await client.patch(
        f"/api/tickets/{ticket_id}/status", headers=headers, json={"action": "CLOSE"}
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "CLOSED"

    logs = (
        await client.get(f"/api/tickets/{ticket_id}/logs", headers=headers)
    ).json()["data"]
    assert logs[-1]["action"] == "CLOSE"
    assert logs[-1]["fromStatus"] == "RESOLVED"
    assert logs[-1]["toStatus"] == "CLOSED"
    assert logs[-1]["detail"] == "学生验收关闭"


async def test_flow_004_close_pending_returns_409(seeded_client):
    """未到 RESOLVED 不能验收关闭，返回 409。"""
    client, Session = seeded_client
    headers = await auth_headers(client)
    ticket_id = await _create_owned_ticket(client, Session, status="PENDING")

    resp = await client.patch(
        f"/api/tickets/{ticket_id}/status", headers=headers, json={"action": "CLOSE"}
    )
    assert resp.status_code == 409
    assert resp.json()["code"] == 409


@pytest.mark.parametrize("action", ["ACCEPT", "RESOLVE"])
async def test_flow_004_non_student_action_is_403(seeded_client, action):
    """ACCEPT/RESOLVE 属维修/管理员轮次，学生调用返回 403。"""
    client, Session = seeded_client
    headers = await auth_headers(client)
    ticket_id = await _create_owned_ticket(client, Session, status="PENDING")

    resp = await client.patch(
        f"/api/tickets/{ticket_id}/status", headers=headers, json={"action": action}
    )
    assert resp.status_code == 403
    assert resp.json()["code"] == 403


async def test_flow_004_invalid_action_is_422(seeded_client):
    client, Session = seeded_client
    headers = await auth_headers(client)
    ticket_id = await _create_owned_ticket(client, Session, status="PENDING")

    resp = await client.patch(
        f"/api/tickets/{ticket_id}/status", headers=headers, json={"action": "DELETE"}
    )
    assert resp.status_code == 422
    assert resp.json()["code"] == 422