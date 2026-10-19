"""FLOW-003/004 管理员异常状态迁移测试（管理端轮次）。

覆盖：管理员解决任意 PROCESSING（无需本人负责）、代为关闭 RESOLVED、
取消 PENDING、错误状态 409、ASSIGN 必须走指派接口 403。
"""

from tests.admin.helpers import auth_headers, make_ticket, user_id


async def _ticket(
    client, Session, *, status: str, assignee: str | None = None, ticket_no: str = "REP-0001"
) -> int:
    student_id = await user_id(Session, "student")
    assignee_id = await user_id(Session, assignee) if assignee else None
    async with Session() as session:
        ticket = make_ticket(
            student_id,
            ticket_no=ticket_no,
            status=status,
            assignee_id=assignee_id,
        )
        session.add(ticket)
        await session.commit()
        await session.refresh(ticket)
        return ticket.id


async def test_flow_003_admin_resolves_any_processing(seeded_client):
    """管理员可解决任意 PROCESSING 工单（异常处理），写 RESOLVE 日志。"""
    client, Session = seeded_client
    ticket_id = await _ticket(client, Session, status="PROCESSING", assignee="tech")

    headers = await auth_headers(client, "admin")
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
    assert logs[-1]["detail"] == "管理员标记解决"
    assert logs[-1]["actorName"] == "系统管理员"


async def test_flow_004_admin_closes_resolved(seeded_client):
    """管理员代为关闭 RESOLVED 工单，写 CLOSE 日志。"""
    client, Session = seeded_client
    ticket_id = await _ticket(client, Session, status="RESOLVED", assignee="tech")

    headers = await auth_headers(client, "admin")
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
    assert logs[-1]["detail"] == "管理员代为关闭"


async def test_flow_004_admin_cancels_pending(seeded_client):
    """管理员取消 PENDING 工单，写 CANCEL 日志。"""
    client, Session = seeded_client
    ticket_id = await _ticket(client, Session, status="PENDING")

    headers = await auth_headers(client, "admin")
    resp = await client.patch(
        f"/api/tickets/{ticket_id}/status", headers=headers, json={"action": "CANCEL"}
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "CANCELLED"

    logs = (
        await client.get(f"/api/tickets/{ticket_id}/logs", headers=headers)
    ).json()["data"]
    assert logs[-1]["action"] == "CANCEL"
    assert logs[-1]["fromStatus"] == "PENDING"
    assert logs[-1]["toStatus"] == "CANCELLED"
    assert logs[-1]["detail"] == "管理员取消工单"


async def test_flow_003_004_admin_wrong_status_returns_409(seeded_client):
    """错误状态执行 RESOLVE/CLOSE/CANCEL 一律返回 409，状态不变。"""
    client, Session = seeded_client
    headers = await auth_headers(client, "admin")

    pending_id = await _ticket(client, Session, status="PENDING", ticket_no="REP-0001")
    resp = await client.patch(
        f"/api/tickets/{pending_id}/status", headers=headers, json={"action": "RESOLVE"}
    )
    assert resp.status_code == 409

    processing_id = await _ticket(
        client, Session, status="PROCESSING", assignee="tech", ticket_no="REP-0002"
    )
    resp = await client.patch(
        f"/api/tickets/{processing_id}/status",
        headers=headers,
        json={"action": "CLOSE"},
    )
    assert resp.status_code == 409
    resp = await client.patch(
        f"/api/tickets/{processing_id}/status",
        headers=headers,
        json={"action": "CANCEL"},
    )
    assert resp.status_code == 409

    detail = (
        await client.get(f"/api/tickets/{processing_id}", headers=headers)
    ).json()["data"]
    assert detail["status"] == "PROCESSING"


async def test_flow_002_admin_assign_via_status_is_403(seeded_client):
    """ASSIGN 动作必须走 /assignee 指派接口，状态接口返回 403。"""
    client, Session = seeded_client
    ticket_id = await _ticket(client, Session, status="PENDING")
    headers = await auth_headers(client, "admin")
    resp = await client.patch(
        f"/api/tickets/{ticket_id}/status", headers=headers, json={"action": "ASSIGN"}
    )
    assert resp.status_code == 403
    assert resp.json()["code"] == 403
