"""S3 测试数据构造与登录助手（TKT-002 / FLOW-004 / TKT-003 / AUD-001）。

与 S2 的 query/helpers.py 同构；本切片自带一套，避免跨切片共享文件依赖。
"""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comment import TicketComment
from app.models.log import TicketLog
from app.models.ticket import Ticket
from app.models.user import User

BASE_TIME = datetime(2026, 8, 1, tzinfo=timezone.utc)


def make_ticket(
    reporter_id: int,
    *,
    ticket_no: str,
    title: str = "测试工单",
    description: str = "这是测试工单的描述内容",
    category: str = "教学设备",
    location: str = "实训楼 A-302",
    priority: str = "MEDIUM",
    status: str = "PENDING",
    assignee_id: int | None = None,
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
) -> Ticket:
    return Ticket(
        ticket_no=ticket_no,
        title=title,
        description=description,
        category=category,
        location=location,
        priority=priority,
        status=status,
        reporter_id=reporter_id,
        assignee_id=assignee_id,
        created_at=created_at or BASE_TIME,
        updated_at=updated_at or BASE_TIME,
    )


async def add_tickets(session: AsyncSession, *tickets: Ticket) -> None:
    session.add_all(tickets)
    await session.commit()


async def add_log(
    session: AsyncSession,
    *,
    ticket_id: int,
    actor_id: int,
    action: str,
    from_status: str | None = None,
    to_status: str | None = None,
    detail: str | None = None,
    created_at: datetime | None = None,
) -> None:
    session.add(
        TicketLog(
            ticket_id=ticket_id,
            actor_id=actor_id,
            action=action,
            from_status=from_status,
            to_status=to_status,
            detail=detail,
            created_at=created_at or BASE_TIME,
        )
    )
    await session.commit()


async def add_comment(
    session: AsyncSession,
    *,
    ticket_id: int,
    author_id: int,
    content: str,
    created_at: datetime | None = None,
) -> None:
    session.add(
        TicketComment(
            ticket_id=ticket_id,
            author_id=author_id,
            content=content,
            created_at=created_at or BASE_TIME,
        )
    )
    await session.commit()


async def auth_headers(client, username: str = "student") -> dict:
    resp = await client.post(
        "/api/auth/login", json={"username": username, "password": "123456"}
    )
    assert resp.status_code == 200
    return {"Authorization": f"Bearer {resp.json()['data']['token']}"}


async def user_id(Session, username: str) -> int:
    async with Session() as session:
        user = await session.scalar(select(User).where(User.username == username))
    assert user is not None
    return user.id


async def ticket_id_by_no(Session, ticket_no: str) -> int:
    async with Session() as session:
        tid = await session.scalar(
            select(Ticket.id).where(Ticket.ticket_no == ticket_no)
        )
    assert tid is not None
    return tid