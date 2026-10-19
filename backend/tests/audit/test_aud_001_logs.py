"""AUD-001 操作日志时间线测试（S3，成员 C）。

覆盖：鉴权 401、不存在/他人工单 404、日志按时间正序、
关键动作记录（CREATE/CANCEL/CLOSE/COMMENT），服务端持久化不允许前端伪造。
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.models.log import TicketLog
from app.models.ticket import Ticket
from app.models.user import User

BASE_TIME = datetime(2026, 8, 1, tzinfo=timezone.utc)


async def _login(client, username: str = "student") -> dict:
    resp = await client.post(
        "/api/auth/login", json={"username": username, "password": "123456"}
    )
    assert resp.status_code == 200
    return {"Authorization": f"Bearer {resp.json()['data']['token']}"}


async def _user_id(session, username: str) -> int:
    user_id = await session.scalar(select(User.id).where(User.username == username))
    assert user_id is not None
    return user_id


async def _add_ticket_with_logs(
    session,
    *,
    reporter_id: int,
    actions: list[tuple[str, str | None, str | None, str]],
) -> int:
    """插入一张工单和指定动作日志（created_at 按分钟递增，便于断言正序）。"""
    ticket = Ticket(
        ticket_no="REP-0001",
        title="测试工单",
        description="这是测试工单的描述内容",
        category="教学设备",
        location="实训楼 A-302",
        priority="MEDIUM",
        status="PENDING",
        reporter_id=reporter_id,
        created_at=BASE_TIME,
        updated_at=BASE_TIME,
    )
    session.add(ticket)
    await session.flush()
    for i, (action, from_status, to_status, detail) in enumerate(actions):
        session.add(
            TicketLog(
                ticket_id=ticket.id,
                actor_id=reporter_id,
                action=action,
                from_status=from_status,
                to_status=to_status,
                detail=detail,
                created_at=BASE_TIME + timedelta(minutes=i + 1),
            )
        )
    await session.commit()
    await session.refresh(ticket)
    return ticket.id


async def test_aud_001_requires_login(client):
    resp = await client.get("/api/tickets/1/logs")
    assert resp.status_code == 401
    assert resp.json()["code"] == 401


async def test_aud_001_not_found_returns_404(client, session):
    headers = await _login(client)
    resp = await client.get("/api/tickets/999/logs", headers=headers)
    assert resp.status_code == 404


async def test_aud_001_other_users_ticket_is_404(client, session):
    """数据范围：技术人员的工单对学生不可见，返回 404。"""
    headers = await _login(client)  # student
    tech_id = await _user_id(session, "tech")
    ticket_id = await _add_ticket_with_logs(
        session,
        reporter_id=tech_id,
        actions=[("CREATE", None, "PENDING", "提交报修申请")],
    )
    resp = await client.get(f"/api/tickets/{ticket_id}/logs", headers=headers)
    assert resp.status_code == 404


async def test_aud_001_logs_ordered_by_time_asc(client, session):
    headers = await _login(client)
    student_id = await _user_id(session, "student")
    ticket_id = await _add_ticket_with_logs(
        session,
        reporter_id=student_id,
        actions=[
            ("CREATE", None, "PENDING", "提交报修申请"),
            ("CANCEL", "PENDING", "CANCELLED", "学生取消工单"),
        ],
    )
    resp = await client.get(f"/api/tickets/{ticket_id}/logs", headers=headers)
    assert resp.status_code == 200
    logs = resp.json()["data"]
    assert [log["action"] for log in logs] == ["CREATE", "CANCEL"]
    assert logs[0]["fromStatus"] is None
    assert logs[0]["toStatus"] == "PENDING"
    assert logs[0]["detail"] == "提交报修申请"
    assert logs[1]["fromStatus"] == "PENDING"
    assert logs[1]["toStatus"] == "CANCELLED"
    assert logs[1]["actorName"] == "学生用户"
    assert logs[0]["createdAt"] <= logs[1]["createdAt"]


async def test_aud_001_close_and_comment_logged(client, session):
    headers = await _login(client)
    student_id = await _user_id(session, "student")
    ticket_id = await _add_ticket_with_logs(
        session,
        reporter_id=student_id,
        actions=[
            ("CREATE", None, "PENDING", "提交报修申请"),
            ("COMMENT", None, None, "新增处理留言"),
            ("CLOSE", "RESOLVED", "CLOSED", "学生验收关闭"),
        ],
    )
    resp = await client.get(f"/api/tickets/{ticket_id}/logs", headers=headers)
    logs = resp.json()["data"]
    assert [log["action"] for log in logs] == ["CREATE", "COMMENT", "CLOSE"]
    assert logs[2]["detail"] == "学生验收关闭"
    assert logs[2]["fromStatus"] == "RESOLVED"
    assert logs[2]["toStatus"] == "CLOSED"


async def test_aud_001_logs_are_server_side_not_client_forged(client, session):
    """日志只能由服务端在关键动作时写入：直接插入的工单无 CREATE 日志，详情页不返回伪造内容。"""
    headers = await _login(client)
    student_id = await _user_id(session, "student")
    async with session:
        ticket = Ticket(
            ticket_no="REP-0001",
            title="测试工单",
            description="这是测试工单的描述内容",
            category="教学设备",
            location="实训楼 A-302",
            priority="MEDIUM",
            status="PENDING",
            reporter_id=student_id,
            created_at=BASE_TIME,
            updated_at=BASE_TIME,
        )
        session.add(ticket)
        await session.commit()
        await session.refresh(ticket)
        ticket_id = ticket.id
    resp = await client.get(f"/api/tickets/{ticket_id}/logs", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["data"] == []