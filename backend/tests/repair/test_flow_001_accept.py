"""FLOW-001 维修接单测试（BE2 轮次）。

覆盖：AC-04 接单成功（PENDING→PROCESSING、负责人=本人、写 ACCEPT 日志）、
已指派工单接单 409、非 PENDING 接单 409、并发冲突 409。
"""

from tests.repair.helpers import auth_headers, make_ticket, user_id


async def _pool_ticket(client, Session, *, status: str = "PENDING", assignee: str | None = None) -> int:
    student_id = await user_id(Session, "student")
    assignee_id = await user_id(Session, assignee) if assignee else None
    async with Session() as session:
        ticket = make_ticket(
            student_id,
            ticket_no="REP-0001",
            status=status,
            assignee_id=assignee_id,
        )
        session.add(ticket)
        await session.commit()
        await session.refresh(ticket)
        return ticket.id


async def test_flow_001_tech_accepts_pool_ticket(seeded_client):
    """AC-04：维修人员认领 PENDING 工单 → PROCESSING，负责人=本人，写 ACCEPT 日志。"""
    client, Session = seeded_client
    tech_id = await user_id(Session, "tech")
    ticket_id = await _pool_ticket(client, Session)

    headers = await auth_headers(client, "tech")
    resp = await client.patch(
        f"/api/tickets/{ticket_id}/status", headers=headers, json={"action": "ACCEPT"}
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["status"] == "PROCESSING"
    assert data["assigneeId"] == tech_id
    assert data["assigneeName"] == "维修人员"
    assert data["assignedBy"] == tech_id
    assert data["assignedAt"] is not None

    logs = (
        await client.get(f"/api/tickets/{ticket_id}/logs", headers=headers)
    ).json()["data"]
    assert logs[-1]["action"] == "ACCEPT"
    assert logs[-1]["fromStatus"] == "PENDING"
    assert logs[-1]["toStatus"] == "PROCESSING"
    assert logs[-1]["detail"] == "维修人员接单"
    assert logs[-1]["actorName"] == "维修人员"


async def test_flow_001_accept_already_assigned_returns_409(seeded_client):
    """工单已被他人接取/指派后，其他维修人员接单返回 409。"""
    client, Session = seeded_client
    ticket_id = await _pool_ticket(client, Session, assignee="tech")

    headers = await auth_headers(client, "tech2")
    resp = await client.patch(
        f"/api/tickets/{ticket_id}/status", headers=headers, json={"action": "ACCEPT"}
    )
    assert resp.status_code == 409
    assert resp.json()["code"] == 409


async def test_flow_001_accept_non_pending_returns_409(seeded_client):
    """PROCESSING/RESOLVED 等非 PENDING 工单不能接单，返回 409。"""
    client, Session = seeded_client
    ticket_id = await _pool_ticket(client, Session, status="PROCESSING", assignee="tech")

    headers = await auth_headers(client, "tech2")
    resp = await client.patch(
        f"/api/tickets/{ticket_id}/status", headers=headers, json={"action": "ACCEPT"}
    )
    assert resp.status_code == 409


async def test_flow_001_concurrent_accept_second_wins_409(seeded_client):
    """并发接单：第一人成功后，第二人接单返回 409（AC-04 并发口径）。"""
    client, Session = seeded_client
    ticket_id = await _pool_ticket(client, Session)

    first = await auth_headers(client, "tech")
    resp = await client.patch(
        f"/api/tickets/{ticket_id}/status", headers=first, json={"action": "ACCEPT"}
    )
    assert resp.status_code == 200

    second = await auth_headers(client, "tech2")
    resp = await client.patch(
        f"/api/tickets/{ticket_id}/status", headers=second, json={"action": "ACCEPT"}
    )
    assert resp.status_code == 409
