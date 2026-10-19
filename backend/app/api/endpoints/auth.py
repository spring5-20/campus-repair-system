from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User as UserModel
from app.schemas.auth import LoginRequest, TokenResponse, User
from app.schemas.common import ApiResponse
from app.services.auth_service import authenticate_user, issue_token

router = APIRouter()


@router.post(
    "/auth/login",
    response_model=ApiResponse[TokenResponse],
    responses={status.HTTP_401_UNAUTHORIZED: {"description": "账号或密码错误"}},
)
async def login(
    payload: LoginRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[TokenResponse]:
    user = await authenticate_user(session, payload.username, payload.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="账号或密码错误"
        )
    return ApiResponse(
        data=TokenResponse(token=issue_token(user), user=User.model_validate(user))
    )


@router.get(
    "/auth/me",
    response_model=ApiResponse[User],
    responses={status.HTTP_401_UNAUTHORIZED: {"description": "未登录或凭证失效"}},
)
async def me(
    user: Annotated[UserModel, Depends(get_current_user)],
) -> ApiResponse[User]:
    return ApiResponse(data=User.model_validate(user))