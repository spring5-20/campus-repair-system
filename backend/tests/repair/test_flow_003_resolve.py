"""FLOW-003 完成维修测试（BE2 轮次）。

覆盖：AC-07 负责人解决成功（PROCESSING→RESOLVED、写 RESOLVE 日志）、
AC-05 其他维修人员解决返回 403 且状态不变、错误状态迁移 409。
"""

from tests.repair.helpers import auth_headers, make_ticket, user_id


async def _processing_ticket(client, Session, *, assignee: str = "tech") -> int:
    student_id = await user_id(Session, "student")
    assignee_id = await user_id(Session, assignee)
    async with Session() as session:
        ticket = make_ticket(
            student_id,
            ticket_no="REP-0001",
            status="PROCESSING",
            assignee_id=assignee_id,
        )
        session.add(ticket)
        await session.commit()
        await session.refresh(ticket)
        return ticket.id


async def test_flow_003_assignee_resolves_processing(seeded_client):
    """AC-07：负责人完成维修 PROCESSING→RESOLVED，写 RESOLVE 日志。"""
    client, Session = seeded_client
    ticket_id = await _processing_ticket(client, Session, assignee="tech")

    headers = await auth_headers(client, "tech")
    resp = await client.patch(
        f"/api/tickets/{ticket_id}/status", headers=headers, json={"action": "RESOLVE"}
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "RESOLVED"

    logs = (
        await client.get(f"/api/tickets/{ticket_id}/logs", headers=headers)
    ).json()["data"]
    assert logs[-1]["action"] == "RESOLVE"
    assert logs[-1]["fromStatus"] == "PROCESSING"
    assert logs[-1]["toStatus"] == "RESOLVED"
    assert logs[-1]["detail"] == "维修完成，等待确认"
    assert logs[-1]["actorName"] == "维修人员"


async def test_flow_003_other_tech_cannot_resolve(seeded_client):
    """AC-05：其他维修人员完成已指派工单返回 403，状态不变。"""
    client, Session = seeded_client
    ticket_id = await _processing_ticket(client, Session, assignee="tech")

    headers = await auth_headers(client, "tech2")
    resp = await client.patch(
        f"/api/tickets/{ticket_id}/status", headers=headers, json={"action": "RESOLVE"}
    )
    assert resp.status_code == 403
    assert resp.json()["code"] == 403

    owner = await auth_headers(client, "tech")
    detail = (
        await client.get(f"/api/tickets/{ticket_id}", headers=owner)
    ).json()["data"]
    assert detail["status"] == "PROCESSING"


async def test_flow_003_resolve_wrong_status_returns_409(seeded_client):
    """非 PROCESSING 状态不能解决，返回 409。"""
    client, Session = seeded_client
    student_id = await user_id(Session, "student")
    tech_id = await user_id(Session, "tech")
    async with Session() as session:
        ticket = make_ticket(
            student_id,
            ticket_no="REP-0001",
            status="RESOLVED",
            assignee_id=tech_id,
        )
        session.add(ticket)
        await session.commit()
        await session.refresh(ticket)
        ticket_id = ticket.id

    headers = await auth_headers(client, "tech")
    resp = await client.patch(
        f"/api/tickets/{ticket_id}/status", headers=headers, json={"action": "RESOLVE"}
    )
    assert resp.status_code == 409


async def test_flow_003_tech_cannot_assign_or_close(seeded_client):
    """ASSIGN/CLOSE 属管理员/学生动作，维修人员调用返回 403。"""
    client, Session = seeded_client
    ticket_id = await _processing_ticket(client, Session, assignee="tech")

    headers = await auth_headers(client, "tech")
    for action in ("ASSIGN", "CLOSE"):
        resp = await client.patch(
            f"/api/tickets/{ticket_id}/status",
            headers=headers,
            json={"action": action},
        )
        assert resp.status_code == 403
