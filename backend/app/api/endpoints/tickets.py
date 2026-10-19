from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, require_role
from app.core.database import get_db
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.ticket import (
    AssigneeRequest,
    CommentCreate,
    PageSize,
    Statistics,
    StatusChangeRequest,
    Ticket,
    TicketComment,
    TicketCreate,
    TicketDetail,
    TicketLog,
    TicketPage,
    TicketScope,
    TicketStatus,
)
from app.services import ticket_service

router = APIRouter()

_UNAUTHORIZED_RESPONSE = {401: {"description": "未登录"}}

# S3 详情/互动接口公共响应：存在性或可见范围问题统一 404。
_DETAIL_RESPONSES = {
    status.HTTP_401_UNAUTHORIZED: {"description": "未登录"},
    status.HTTP_403_FORBIDDEN: {"description": "没有权限执行该操作"},
    status.HTTP_404_NOT_FOUND: {"description": "工单不存在"},
}
_STATUS_RESPONSES = {
    **_DETAIL_RESPONSES,
    status.HTTP_409_CONFLICT: {"description": "工单状态已变化，请刷新后重试"},
}


@router.get(
    "/tickets",
    response_model=ApiResponse[TicketPage],
    responses=_UNAUTHORIZED_RESPONSE,
)  # LIST-001 分页查询（S2）
async def list_tickets(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    pageSize: PageSize = PageSize.TEN,
    scope: TicketScope | None = Query(default=None),
    status: TicketStatus | None = Query(default=None),
    category: str | None = Query(default=None),
    keyword: str | None = Query(default=None),
) -> ApiResponse[TicketPage]:
    data = await ticket_service.list_tickets(
        session,
        user,
        page=page,
        page_size=pageSize.value,
        scope=scope.value if scope else None,
        keyword=keyword,
        status=status.value if status else None,
        category=category,
    )
    return ApiResponse(data=data)


@router.post(
    "/tickets",
    response_model=ApiResponse[Ticket],
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "未登录或凭证失效"},
        status.HTTP_403_FORBIDDEN: {"description": "没有权限执行该操作"},
    },
)  # TKT-001 创建工单（S1）
async def create_ticket_endpoint(
    payload: TicketCreate,
    user: Annotated[User, Depends(require_role("student"))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[Ticket]:
    ticket = await ticket_service.create_ticket(session, user, payload)
    return ApiResponse(data=ticket)


@router.get(
    "/tickets/statistics",
    response_model=ApiResponse[Statistics],
    responses=_UNAUTHORIZED_RESPONSE,
)  # DASH-001 角色范围统计（S2）
async def ticket_statistics(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[Statistics]:
    data = await ticket_service.get_statistics(session, user)
    return ApiResponse(data=data)


@router.get(
    "/tickets/{ticketId}",
    response_model=ApiResponse[TicketDetail],
    responses=_DETAIL_RESPONSES,
)  # TKT-002 工单详情（S3）
async def ticket_detail(
    ticketId: Annotated[int, Path(alias="ticketId")],
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[TicketDetail]:
    data = await ticket_service.get_ticket_detail(session, user, ticketId)
    return ApiResponse(data=data)


@router.patch(
    "/tickets/{ticketId}/status",
    response_model=ApiResponse[Ticket],
    responses=_STATUS_RESPONSES,
)  # FLOW-004 学生取消/验收关闭（S3）
async def change_status(
    payload: StatusChangeRequest,
    ticketId: Annotated[int, Path(alias="ticketId")],
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[Ticket]:
    data = await ticket_service.change_ticket_status(
        session, user, ticketId, payload.action
    )
    return ApiResponse(data=data)


@router.patch(
    "/tickets/{ticketId}/assignee",
    response_model=ApiResponse[Ticket],
    responses=_STATUS_RESPONSES,
)  # FLOW-002 管理员指派（管理端轮次）
async def assign_ticket(
    payload: AssigneeRequest,
    ticketId: Annotated[int, Path(alias="ticketId")],
    user: Annotated[User, Depends(require_role("admin"))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[Ticket]:
    data = await ticket_service.assign_ticket(session, user, ticketId, payload)
    return ApiResponse(data=data)


@router.post(
    "/tickets/{ticketId}/comments",
    response_model=ApiResponse[TicketComment],
    responses=_DETAIL_RESPONSES,
)  # TKT-003 处理留言（S3）
async def add_comment(
    payload: CommentCreate,
    ticketId: Annotated[int, Path(alias="ticketId")],
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[TicketComment]:
    data = await ticket_service.add_ticket_comment(session, user, ticketId, payload)
    return ApiResponse(data=data)


@router.get(
    "/tickets/{ticketId}/logs",
    response_model=ApiResponse[list[TicketLog]],
    responses=_DETAIL_RESPONSES,
)  # AUD-001 操作日志（S3）
async def ticket_logs(
    ticketId: Annotated[int, Path(alias="ticketId")],
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[list[TicketLog]]:
    data = await ticket_service.get_ticket_logs(session, user, ticketId)
    return ApiResponse(data=data)
