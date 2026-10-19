"""用户相关业务逻辑（管理端用户列表等）。"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories import user_repository


async def list_users(
    session: AsyncSession, role: str | None = None
) -> list[User]:
    """USER-001：按角色筛选用户列表（FLOW-002 指派下拉使用）。"""
    return await user_repository.list_users(session, role=role)
