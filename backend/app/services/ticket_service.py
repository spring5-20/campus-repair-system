"""Business logic for tickets.

P0 implementation lands incrementally:
- S1（成员 A）: create ticket (TKT-001): counter ticketNo, PENDING, CREATE log
- S2（成员 B）: query (LIST-001) and statistics (DASH-001)
- S3（成员 C）: detail, transitions, comments, logs (TKT-002/FLOW-004/TKT-003/AUD-001)
"""

import math
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.log import TicketLog
from app.models.ticket import Ticket as TicketModel
from app.models.user import User
from app.repositories import ticket_repository
from app.repositories import user_repository
from app.repositories.ticket_repository import next_ticket_no
from app.schemas.common import Page
from app.schemas.ticket import (
    AssigneeRequest,
    CommentCreate,
    Statistics,
    Ticket,
    TicketAction,
    TicketComment,
    TicketCreate,
    TicketDetail,
    TicketLog as TicketLogOut,
    TicketStatus,
)


def to_ticket_out(
    ticket: TicketModel, reporter_name: str, assignee_name: str | None = None
) -> Ticket:
    """Map a Ticket row to the API shape (reused by LIST-001/TKT-001/TKT-002 slices)."""
    return Ticket(
        id=ticket.id,
        ticket_no=ticket.ticket_no,
        title=ticket.title,
        description=ticket.description,
        category=ticket.category,
        location=ticket.location,
        priority=ticket.priority,
        status=ticket.status,
        reporter_id=ticket.reporter_id,
        reporter_name=reporter_name,
        assignee_id=ticket.assignee_id,
        assignee_name=assignee_name,
        assigned_by=ticket.assigned_by,
        assigned_at=ticket.assigned_at,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
    )


async def create_ticket(
    session: AsyncSession, user: User, payload: TicketCreate
) -> Ticket:
    """Create a student ticket: sequential ticketNo + PENDING + CREATE log (TKT-001, AC-01)."""
    ticket_no = await next_ticket_no(session)
    ticket = TicketModel(
        ticket_no=ticket_no,
        title=payload.title,
        description=payload.description,
        category=payload.category,
        location=payload.location,
        priority=payload.priority.value,
        status=TicketStatus.PENDING.value,
        reporter_id=user.id,
    )
    session.add(ticket)
    await session.flush()
    session.add(
        TicketLog(
            ticket_id=ticket.id,
            actor_id=user.id,
            action="CREATE",
            from_status=None,
            to_status=TicketStatus.PENDING.value,
            detail="提交报修申请",
        )
    )
    await session.commit()
    await session.refresh(ticket)
    return to_ticket_out(ticket, reporter_name=user.display_name)


async def list_tickets(
    session: AsyncSession,
    user: User,
    *,
    scope: str | None = None,
    page: int = 1,
    page_size: int = 10,
    keyword: str | None = None,
    status: str | None = None,
    category: str | None = None,
) -> Page[Ticket]:
    """LIST-001：按角色数据范围分页查询。

    学生=本人提交；维修=工单池（PENDING 未指派）+ 指派给本人，可用 scope
    进一步收窄（pool/mine）；管理员=全部。
    """
    if user.role == "student":
        rows, total = await ticket_repository.list_tickets_by_reporter(
            session,
            user.id,
            keyword=keyword,
            status=status,
            category=category,
            page=page,
            page_size=page_size,
        )
    elif user.role == "tech":
        rows, total = await ticket_repository.list_tickets_by_tech(
            session,
            user.id,
            scope=scope,
            keyword=keyword,
            status=status,
            category=category,
            page=page,
            page_size=page_size,
        )
    else:
        rows, total = await ticket_repository.list_all_tickets(
            session,
            keyword=keyword,
            status=status,
            category=category,
            page=page,
            page_size=page_size,
        )
    items = [
        to_ticket_out(ticket, reporter_name, assignee_name)
        for ticket, reporter_name, assignee_name in rows
    ]
    pages = math.ceil(total / page_size) if total else 0
    return Page(
        items=items, total=total, page=page, page_size=page_size, pages=pages
    )


async def get_statistics(session: AsyncSession, user: User) -> Statistics:
    """DASH-001：角色统计口径，与列表数据范围一致，不受分页影响。

    closureRate = closed / 全部可见工单（含 cancelled），取整百分比。
    highOpen = HIGH 优先级且状态非 CLOSED/CANCELLED。
    """
    if user.role == "student":
        counts = await ticket_repository.count_tickets_by_reporter_status(
            session, user.id
        )
        high_open = await ticket_repository.count_high_open_by_reporter(
            session, user.id
        )
    elif user.role == "tech":
        counts = await ticket_repository.count_tickets_by_tech_status(
            session, user.id
        )
        high_open = await ticket_repository.count_high_open_by_tech(session, user.id)
    else:
        counts = await ticket_repository.count_tickets_all_status(session)
        high_open = await ticket_repository.count_high_open_all(session)
    total = sum(counts.values())
    closed = counts.get("CLOSED", 0)
    closure_rate = round(closed / total * 100) if total else 0.0
    return Statistics(
        total=total,
        pending=counts.get("PENDING", 0),
        processing=counts.get("PROCESSING", 0),
        resolved=counts.get("RESOLVED", 0),
        closed=closed,
        cancelled=counts.get("CANCELLED", 0),
        high_open=high_open,
        closure_rate=float(closure_rate),
    )


# 学生可执行的状态迁移（FLOW-004）：action -> (期望状态, 目标状态, 日志详情)。
# 其余 action（ACCEPT/ASSIGN/RESOLVE）属维修/管理员轮次，学生调用返回 403。
_STUDENT_TRANSITIONS: dict[TicketAction, tuple[str, str, str]] = {
    TicketAction.CANCEL: (
        TicketStatus.PENDING.value,
        TicketStatus.CANCELLED.value,
        "学生取消工单",
    ),
    TicketAction.CLOSE: (
        TicketStatus.RESOLVED.value,
        TicketStatus.CLOSED.value,
        "学生验收关闭",
    ),
}


def _is_ticket_visible(ticket: TicketModel, user: User) -> bool:
    """角色数据范围（LIST-001/TKT-002/TKT-003/AUD-001 共用）。

    学生=本人提交；维修=工单池（PENDING 未指派）或指派给本人；管理员=全部。
    """
    if user.role == "student":
        return ticket.reporter_id == user.id
    if user.role == "tech":
        return (
            ticket.status == TicketStatus.PENDING.value and ticket.assignee_id is None
        ) or ticket.assignee_id == user.id
    return True


async def get_ticket_detail(
    session: AsyncSession, user: User, ticket_id: int
) -> TicketDetail:
    """TKT-002：工单详情（基础信息 + 留言 + 操作时间线）。

    数据范围与列表一致：学生=本人，维修=工单池或本人任务，其余一律 404（不泄露存在性）。
    """
    row = await ticket_repository.get_ticket_with_names(session, ticket_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "工单不存在")
    ticket, reporter_name, assignee_name = row
    if not _is_ticket_visible(ticket, user):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "工单不存在")
    base = to_ticket_out(ticket, reporter_name, assignee_name)
    comments = [
        TicketComment(
            id=c.id,
            ticket_id=c.ticket_id,
            author_id=c.author_id,
            author_name=name,
            content=c.content,
            created_at=c.created_at,
        )
        for c, name in await ticket_repository.list_comments_with_author(
            session, ticket_id
        )
    ]
    logs = [
        TicketLogOut(
            id=l.id,
            ticket_id=l.ticket_id,
            actor_id=l.actor_id,
            actor_name=name,
            action=l.action,
            from_status=l.from_status,
            to_status=l.to_status,
            detail=l.detail,
            created_at=l.created_at,
        )
        for l, name in await ticket_repository.list_logs_with_actor(session, ticket_id)
    ]
    return TicketDetail(**base.model_dump(), comments=comments, logs=logs)


async def auto_close_stale_resolved(
    session: AsyncSession, timeout_hours: int = 48
) -> int:
    """Scheduler：关闭进入 RESOLVED 超过 timeout_hours 仍未确认的工单（FLOW-004 自动化）。

    计时基准复用 updated_at（进入 RESOLVED 时已刷新）；条件更新防并发，命中才写 CLOSE 日志。
    操作人复用 admin 账号；无 admin 账号时跳过处理返回 0。
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=timeout_hours)
    stale = await ticket_repository.list_resolved_older_than(session, cutoff)
    admins = await user_repository.list_users(session, role="admin")
    if not stale or not admins:
        return 0
    admin_id = admins[0].id
    closed = 0
    for ticket in stale:
        updated = await ticket_repository.update_status_if(
            session, ticket.id, TicketStatus.RESOLVED.value, TicketStatus.CLOSED.value
        )
        if not updated:
            continue
        session.add(
            TicketLog(
                ticket_id=ticket.id,
                actor_id=admin_id,
                action="CLOSE",
                from_status=TicketStatus.RESOLVED.value,
                to_status=TicketStatus.CLOSED.value,
                detail=f"超过{timeout_hours}小时未确认，系统自动关闭",
            )
        )
        closed += 1
    await session.commit()
    return closed


async def change_ticket_status(
    session: AsyncSession, user: User, ticket_id: int, action: TicketAction
) -> Ticket:
    """FLOW-001..004：按角色执行状态迁移。

    权限顺序：工单不存在 404 -> 角色 action 白名单 403 -> 条件更新 409。
    """
    ticket = await ticket_repository.get_ticket_by_id(session, ticket_id)
    if ticket is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "工单不存在")
    if user.role == "student":
        return await _change_status_as_student(session, user, ticket, action)
    if user.role == "tech":
        return await _change_status_as_tech(session, user, ticket, action)
    return await _change_status_as_admin(session, user, ticket, action)


async def _change_status_as_student(
    session: AsyncSession, user: User, ticket: TicketModel, action: TicketAction
) -> Ticket:
    """FLOW-004：学生取消 PENDING / 验收关闭 RESOLVED。"""
    if ticket.reporter_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "工单不存在")
    transition = _STUDENT_TRANSITIONS.get(action)
    if transition is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "没有权限执行该操作")
    from_status, to_status, detail = transition
    updated = await ticket_repository.update_status_if(
        session, ticket.id, from_status, to_status
    )
    if not updated:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "当前工单状态已变化，请刷新后重试"
        )
    session.add(
        TicketLog(
            ticket_id=ticket.id,
            actor_id=user.id,
            action=action.value,
            from_status=from_status,
            to_status=to_status,
            detail=detail,
        )
    )
    await session.commit()
    await session.refresh(ticket)
    return await _to_ticket_out_with_names(session, ticket)


async def _change_status_as_tech(
    session: AsyncSession, user: User, ticket: TicketModel, action: TicketAction
) -> Ticket:
    """FLOW-001 接单 / FLOW-003 完成维修（AC-04 / AC-05 / AC-07）。"""
    if action == TicketAction.ACCEPT:
        if (
            ticket.status != TicketStatus.PENDING.value
            or ticket.assignee_id is not None
        ):
            raise HTTPException(
                status.HTTP_409_CONFLICT, "工单已被接取或状态已变化，请刷新后重试"
            )
        updated = await ticket_repository.accept_ticket_if(
            session, ticket.id, user.id
        )
        from_status, to_status, detail = (
            TicketStatus.PENDING.value,
            TicketStatus.PROCESSING.value,
            "维修人员接单",
        )
    elif action == TicketAction.RESOLVE:
        if ticket.assignee_id != user.id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "没有权限执行该操作")
        if ticket.status != TicketStatus.PROCESSING.value:
            raise HTTPException(
                status.HTTP_409_CONFLICT, "当前工单状态已变化，请刷新后重试"
            )
        updated = await ticket_repository.resolve_ticket_if(
            session, ticket.id, user.id
        )
        from_status, to_status, detail = (
            TicketStatus.PROCESSING.value,
            TicketStatus.RESOLVED.value,
            "维修完成，等待确认",
        )
    else:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "没有权限执行该操作")
    if not updated:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "当前工单状态已变化，请刷新后重试"
        )
    session.add(
        TicketLog(
            ticket_id=ticket.id,
            actor_id=user.id,
            action=action.value,
            from_status=from_status,
            to_status=to_status,
            detail=detail,
        )
    )
    await session.commit()
    await session.refresh(ticket)
    return await _to_ticket_out_with_names(session, ticket)


async def _change_status_as_admin(
    session: AsyncSession, user: User, ticket: TicketModel, action: TicketAction
) -> Ticket:
    """FLOW-003/004：管理员异常处理（解决/关闭/取消任意可见工单）。

    指派（ASSIGN）不走状态接口，必须调用 /assignee（FLOW-002）。
    """
    if action == TicketAction.RESOLVE:
        if ticket.status != TicketStatus.PROCESSING.value:
            raise HTTPException(
                status.HTTP_409_CONFLICT, "当前工单状态已变化，请刷新后重试"
            )
        from_status, to_status, detail = (
            TicketStatus.PROCESSING.value,
            TicketStatus.RESOLVED.value,
            "管理员标记解决",
        )
        updated = await ticket_repository.update_status_if(
            session, ticket.id, from_status, to_status
        )
    elif action == TicketAction.CLOSE:
        if ticket.status != TicketStatus.RESOLVED.value:
            raise HTTPException(
                status.HTTP_409_CONFLICT, "当前工单状态已变化，请刷新后重试"
            )
        from_status, to_status, detail = (
            TicketStatus.RESOLVED.value,
            TicketStatus.CLOSED.value,
            "管理员代为关闭",
        )
        updated = await ticket_repository.update_status_if(
            session, ticket.id, from_status, to_status
        )
    elif action == TicketAction.CANCEL:
        if ticket.status != TicketStatus.PENDING.value:
            raise HTTPException(
                status.HTTP_409_CONFLICT, "当前工单状态已变化，请刷新后重试"
            )
        from_status, to_status, detail = (
            TicketStatus.PENDING.value,
            TicketStatus.CANCELLED.value,
            "管理员取消工单",
        )
        updated = await ticket_repository.update_status_if(
            session, ticket.id, from_status, to_status
        )
    else:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "指派请使用工单指派接口"
        )
    if not updated:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "当前工单状态已变化，请刷新后重试"
        )
    session.add(
        TicketLog(
            ticket_id=ticket.id,
            actor_id=user.id,
            action=action.value,
            from_status=from_status,
            to_status=to_status,
            detail=detail,
        )
    )
    await session.commit()
    await session.refresh(ticket)
    return await _to_ticket_out_with_names(session, ticket)


async def _to_ticket_out_with_names(
    session: AsyncSession, ticket: TicketModel
) -> Ticket:
    """状态变更提交后重新取报修人/负责人姓名并映射为 API 输出。"""
    row = await ticket_repository.get_ticket_with_names(session, ticket.id)
    assert row is not None
    _, reporter_name, assignee_name = row
    return to_ticket_out(ticket, reporter_name, assignee_name)


async def assign_ticket(
    session: AsyncSession, user: User, ticket_id: int, payload: AssigneeRequest
) -> Ticket:
    """FLOW-002：管理员指派 PENDING 工单给维修人员（AC-06）。

    校验顺序：工单存在 -> 指派对象存在 -> 指派对象为维修人员 -> 状态可指派 ->
    条件更新（并发 409）；与 ASSIGN 日志同一事务。
    """
    ticket = await ticket_repository.get_ticket_by_id(session, ticket_id)
    if ticket is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "工单不存在")
    assignee = await user_repository.get_user_by_id(session, payload.assignee_id)
    if assignee is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "指派对象不存在")
    if assignee.role != "tech":
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "指派对象必须是维修人员"
        )
    if ticket.status != TicketStatus.PENDING.value or ticket.assignee_id is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "工单已被接取或状态已变化，请刷新后重试"
        )
    updated = await ticket_repository.assign_ticket_if(
        session, ticket.id, assignee.id, user.id
    )
    if not updated:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "当前工单状态已变化，请刷新后重试"
        )
    session.add(
        TicketLog(
            ticket_id=ticket.id,
            actor_id=user.id,
            action="ASSIGN",
            from_status=TicketStatus.PENDING.value,
            to_status=TicketStatus.PROCESSING.value,
            detail=f"管理员指派给{assignee.display_name}",
        )
    )
    await session.commit()
    await session.refresh(ticket)
    return await _to_ticket_out_with_names(session, ticket)


async def add_ticket_comment(
    session: AsyncSession, user: User, ticket_id: int, payload: CommentCreate
) -> TicketComment:
    """TKT-003：新增留言并写 COMMENT 日志（AC-10 纯空格在 schema 层拦截为 422）。"""
    ticket = await ticket_repository.get_ticket_by_id(session, ticket_id)
    if ticket is None or not _is_ticket_visible(ticket, user):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "工单不存在")
    comment = await ticket_repository.create_comment(
        session, ticket_id, user.id, payload.content
    )
    session.add(
        TicketLog(
            ticket_id=ticket_id,
            actor_id=user.id,
            action="COMMENT",
            from_status=None,
            to_status=None,
            detail="新增处理留言",
        )
    )
    await session.commit()
    await session.refresh(comment)
    return TicketComment(
        id=comment.id,
        ticket_id=comment.ticket_id,
        author_id=comment.author_id,
        author_name=user.display_name,
        content=comment.content,
        created_at=comment.created_at,
    )


async def get_ticket_logs(
    session: AsyncSession, user: User, ticket_id: int
) -> list[TicketLogOut]:
    """AUD-001：操作日志时间线（按时间正序），仅数据范围内可见。"""
    ticket = await ticket_repository.get_ticket_by_id(session, ticket_id)
    if ticket is None or not _is_ticket_visible(ticket, user):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "工单不存在")
    return [
        TicketLogOut(
            id=l.id,
            ticket_id=l.ticket_id,
            actor_id=l.actor_id,
            actor_name=name,
            action=l.action,
            from_status=l.from_status,
            to_status=l.to_status,
            detail=l.detail,
            created_at=l.created_at,
        )
        for l, name in await ticket_repository.list_logs_with_actor(session, ticket_id)
    ]
