from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


async def get_user_by_id(session: AsyncSession, user_id: int) -> User | None:
    return await session.get(User, user_id)


async def get_user_by_username(session: AsyncSession, username: str) -> User | None:
    return await session.scalar(select(User).where(User.username == username))


async def list_users(
    session: AsyncSession, role: str | None = None
) -> list[User]:
    """USER-001：按角色筛选用户列表（FLOW-002 指派下拉数据源），按 id 正序。"""
    stmt = select(User)
    if role:
        stmt = stmt.where(User.role == role)
    return list((await session.scalars(stmt.order_by(User.id))).all())
