"""FLOW-002 管理员指派测试（管理端轮次）。

覆盖：AC-06 指派成功（PENDING→PROCESSING、负责人/指派人/时间写入、ASSIGN 日志）、
非管理员指派 403、指派对象不存在 404、指派对象非维修人员 422、
非 PENDING/已指派 409、并发冲突 409。
"""

from tests.admin.helpers import auth_headers, make_ticket, user_id


async def _pending_ticket(client, Session, *, status: str = "PENDING", assignee: str | None = None) -> int:
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


async def test_flow_002_admin_assigns_pending_ticket(seeded_client):
    """AC-06：管理员指派 PENDING 工单 → PROCESSING，写 ASSIGN 日志。"""
    client, Session = seeded_client
    tech_id = await user_id(Session, "tech")
    admin_id = await user_id(Session, "admin")
    ticket_id = await _pending_ticket(client, Session)

    headers = await auth_headers(client, "admin")
    resp = await client.patch(
        f"/api/tickets/{ticket_id}/assignee",
        headers=headers,
        json={"assigneeId": tech_id},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["status"] == "PROCESSING"
    assert data["assigneeId"] == tech_id
    assert data["assigneeName"] == "维修人员"
    assert data["assignedBy"] == admin_id
    assert data["assignedAt"] is not None

    logs = (
        await client.get(f"/api/tickets/{ticket_id}/logs", headers=headers)
    ).json()["data"]
    assert logs[-1]["action"] == "ASSIGN"
    assert logs[-1]["fromStatus"] == "PENDING"
    assert logs[-1]["toStatus"] == "PROCESSING"
    assert logs[-1]["detail"] == "管理员指派给维修人员"
    assert logs[-1]["actorName"] == "系统管理员"


async def test_flow_002_non_admin_cannot_assign(seeded_client):
    """学生/维修人员调用指派接口返回 403。"""
    client, Session = seeded_client
    tech_id = await user_id(Session, "tech")
    ticket_id = await _pending_ticket(client, Session)

    for username in ("student", "tech"):
        headers = await auth_headers(client, username)
        resp = await client.patch(
            f"/api/tickets/{ticket_id}/assignee",
            headers=headers,
            json={"assigneeId": tech_id},
        )
        assert resp.status_code == 403
        assert resp.json()["code"] == 403


async def test_flow_002_assignee_not_found_returns_404(seeded_client):
    client, Session = seeded_client
    ticket_id = await _pending_ticket(client, Session)
    headers = await auth_headers(client, "admin")
    resp = await client.patch(
        f"/api/tickets/{ticket_id}/assignee",
        headers=headers,
        json={"assigneeId": 9999},
    )
    assert resp.status_code == 404
    assert resp.json()["code"] == 404


async def test_flow_002_assignee_must_be_tech(seeded_client):
    """指派对象必须是维修人员，否则 422。"""
    client, Session = seeded_client
    student_id = await user_id(Session, "student")
    ticket_id = await _pending_ticket(client, Session)
    headers = await auth_headers(client, "admin")
    resp = await client.patch(
        f"/api/tickets/{ticket_id}/assignee",
        headers=headers,
        json={"assigneeId": student_id},
    )
    assert resp.status_code == 422
    assert resp.json()["code"] == 422


async def test_flow_002_assign_non_pending_returns_409(seeded_client):
    """非 PENDING 工单不能指派，返回 409。"""
    client, Session = seeded_client
    tech_id = await user_id(Session, "tech")
    ticket_id = await _pending_ticket(
        client, Session, status="PROCESSING", assignee="tech"
    )
    headers = await auth_headers(client, "admin")
    resp = await client.patch(
        f"/api/tickets/{ticket_id}/assignee",
        headers=headers,
        json={"assigneeId": tech_id},
    )
    assert resp.status_code == 409


async def test_flow_002_assign_already_assigned_returns_409(seeded_client):
    """工单已被接取/指派后不能再指派，返回 409。"""
    client, Session = seeded_client
    tech_id = await user_id(Session, "tech")
    ticket_id = await _pending_ticket(client, Session, assignee="tech")
    headers = await auth_headers(client, "admin")
    resp = await client.patch(
        f"/api/tickets/{ticket_id}/assignee",
        headers=headers,
        json={"assigneeId": tech_id},
    )
    assert resp.status_code == 409


async def test_flow_002_concurrent_assign_second_returns_409(seeded_client):
    """并发指派：第一次成功后，再次指派返回 409。"""
    client, Session = seeded_client
    tech_id = await user_id(Session, "tech")
    tech2_id = await user_id(Session, "tech2")
    ticket_id = await _pending_ticket(client, Session)

    headers = await auth_headers(client, "admin")
    resp = await client.patch(
        f"/api/tickets/{ticket_id}/assignee",
        headers=headers,
        json={"assigneeId": tech_id},
    )
    assert resp.status_code == 200

    resp = await client.patch(
        f"/api/tickets/{ticket_id}/assignee",
        headers=headers,
        json={"assigneeId": tech2_id},
    )
    assert resp.status_code == 409
