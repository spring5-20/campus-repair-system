from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_role
from app.core.database import get_db
from app.models.user import User as UserModel
from app.schemas.auth import User, UserRole
from app.schemas.common import ApiResponse
from app.services import user_service

router = APIRouter()


@router.get(
    "/users",
    response_model=ApiResponse[list[User]],
    responses={
        401: {"description": "未登录"},
        403: {"description": "没有权限执行该操作"},
    },
)
async def list_users(
    _admin: Annotated[UserModel, Depends(require_role("admin"))],
    session: Annotated[AsyncSession, Depends(get_db)],
    role: UserRole | None = Query(default=None),
) -> ApiResponse[list[User]]:
    """USER-001：用户列表（管理端指派下拉），可按角色筛选。"""
    users = await user_service.list_users(session, role.value if role else None)
    return ApiResponse(data=[User.model_validate(u) for u in users])
