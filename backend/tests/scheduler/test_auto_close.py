"""调度任务：超时未确认的工单自动确认完成（FLOW-004 自动化）。

复用 tests/conftest.py 的 session fixture（student/tech/admin）。直接调用服务函数
auto_close_stale_resolved，断言超时 RESOLVED 被置为 CLOSED 并写 CLOSE 日志；
未超时/非 RESOLVED 状态不受影响；返回关闭数量与预期一致。
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.models.log import TicketLog
from app.models.ticket import Ticket
from app.models.user import User
from app.services.ticket_service import auto_close_stale_resolved

NOW = datetime.now(timezone.utc)


def _make_ticket(
    reporter_id: int, *, ticket_no: str, status: str, updated_at: datetime
) -> Ticket:
    return Ticket(
        ticket_no=ticket_no,
        title="测试工单",
        description="这是测试工单的描述内容",
        category="教学设备",
        location="实训楼 A-302",
        priority="MEDIUM",
        status=status,
        reporter_id=reporter_id,
        created_at=NOW - timedelta(days=10),
        updated_at=updated_at,
    )


async def _status_of(session, ticket_no: str) -> str:
    ticket = await session.scalar(
        select(Ticket).where(Ticket.ticket_no == ticket_no)
    )
    assert ticket is not None
    return ticket.status


async def test_auto_close_stale_resolved(session):
    """AC-01：超时 RESOLVED 被置为 CLOSED，并写 admin 操作的 CLOSE 日志。"""
    student = await session.scalar(select(User).where(User.username == "student"))
    admin = await session.scalar(select(User).where(User.username == "admin"))
    assert student is not None and admin is not None

    stale = _make_ticket(
        student.id, ticket_no="REP-2001", status="RESOLVED",
        updated_at=NOW - timedelta(days=3),
    )
    session.add(stale)
    await session.commit()
    await session.refresh(stale)

    closed = await auto_close_stale_resolved(session, timeout_hours=48)
    assert closed == 1
    assert await _status_of(session, "REP-2001") == "CLOSED"

    log = await session.scalar(
        select(TicketLog).where(TicketLog.ticket_id == stale.id)
    )
    assert log is not None
    assert log.action == "CLOSE"
    assert log.from_status == "RESOLVED"
    assert log.to_status == "CLOSED"
    assert log.actor_id == admin.id
    assert "48" in log.detail


async def test_auto_close_keeps_fresh_resolved(session):
    """AC-02：未超时（1 天）的 RESOLVED 不被关闭，返回 0。"""
    student = await session.scalar(select(User).where(User.username == "student"))
    assert student is not None

    fresh = _make_ticket(
        student.id, ticket_no="REP-2002", status="RESOLVED",
        updated_at=NOW - timedelta(days=1),
    )
    session.add(fresh)
    await session.commit()

    closed = await auto_close_stale_resolved(session, timeout_hours=48)
    assert closed == 0
    assert await _status_of(session, "REP-2002") == "RESOLVED"


async def test_auto_close_ignores_non_resolved(session):
    """AC-03：长时间处于 PROCESSING 的工单不受影响（只处理 RESOLVED）。"""
    student = await session.scalar(select(User).where(User.username == "student"))
    assert student is not None

    processing = _make_ticket(
        student.id, ticket_no="REP-2003", status="PROCESSING",
        updated_at=NOW - timedelta(days=5),
    )
    session.add(processing)
    await session.commit()

    closed = await auto_close_stale_resolved(session, timeout_hours=48)
    assert closed == 0
    assert await _status_of(session, "REP-2003") == "PROCESSING"
