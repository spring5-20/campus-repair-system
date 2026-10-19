"""S2 测试数据构造与登录助手（LIST-001 / DASH-001）。"""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
        created_at=created_at or BASE_TIME,
        updated_at=updated_at or BASE_TIME,
    )


async def add_tickets(session: AsyncSession, *tickets: Ticket) -> None:
    session.add_all(tickets)
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
