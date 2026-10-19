from datetime import datetime

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.models.comment import TicketComment
from app.models.log import TicketLog
from app.models.ticket import SequenceCounter, Ticket
from app.models.user import User

TICKET_NO_COUNTER = "ticket_no"


async def get_ticket_by_id(session: AsyncSession, ticket_id: int) -> Ticket | None:
    return await session.get(Ticket, ticket_id)


async def list_resolved_older_than(
    session: AsyncSession, cutoff: datetime | None
) -> list[Ticket]:
    """Scheduler：筛选滞留超过 cutoff 的 RESOLVED 工单（自动关闭候选，FLOW-004 自动化）。"""
    stmt = select(Ticket).where(
        Ticket.status == "RESOLVED", Ticket.updated_at <= cutoff
    )
    return list((await session.scalars(stmt)).all())


async def get_ticket_by_no(session: AsyncSession, ticket_no: str) -> Ticket | None:
    return await session.scalar(select(Ticket).where(Ticket.ticket_no == ticket_no))


async def next_ticket_no(session: AsyncSession) -> str:
    """Atomically advance the ticket counter and return REP-XXXX (ADR-0002, TKT-001).

    Runs inside the caller's transaction; the UPDATE takes a row lock so
    concurrent creates serialize on both MySQL and SQLite. If the counter row
    is missing (fresh DB without seed), create it first - the seed script
    initializes it in normal setups.
    """
    counter = await session.scalar(
        select(SequenceCounter).where(SequenceCounter.name == TICKET_NO_COUNTER)
    )
    if counter is None:
        session.add(SequenceCounter(name=TICKET_NO_COUNTER, value=0))
        await session.flush()
    await session.execute(
        update(SequenceCounter)
        .where(SequenceCounter.name == TICKET_NO_COUNTER)
        .values(value=SequenceCounter.value + 1)
    )
    value = await session.scalar(
        select(SequenceCounter.value).where(SequenceCounter.name == TICKET_NO_COUNTER)
    )
    if value is None:
        raise RuntimeError("ticket counter is not initialized")
    return f"REP-{value:04d}"


async def list_tickets_by_reporter(
    session: AsyncSession,
    reporter_id: int,
    *,
    keyword: str | None = None,
    status: str | None = None,
    category: str | None = None,
    page: int = 1,
    page_size: int = 10,
) -> tuple[list[tuple[Ticket, str, str | None]], int]:
    """学生数据范围分页查询（LIST-001）。

    keyword 匹配工单编号、标题、位置；排序默认 updatedAt DESC。
    返回 (行, 总数)，每行为 (Ticket, 报修人姓名, 负责人姓名)。
    """
    filters = [Ticket.reporter_id == reporter_id]
    return await _paginate_tickets(
        session,
        filters,
        keyword=keyword,
        status=status,
        category=category,
        page=page,
        page_size=page_size,
    )


async def list_tickets_by_tech(
    session: AsyncSession,
    tech_id: int,
    *,
    scope: str | None = None,
    keyword: str | None = None,
    status: str | None = None,
    category: str | None = None,
    page: int = 1,
    page_size: int = 10,
) -> tuple[list[tuple[Ticket, str, str | None]], int]:
    """维修人员数据范围分页查询（LIST-001）。

    scope=None：工单池（PENDING 未指派）+ 指派给本人；
    scope="pool"：仅工单池；scope="mine"：仅指派给本人。
    排序与 keyword/status/category 筛选规则与学生列表一致。
    """
    if scope == "pool":
        filters = [
            Ticket.status == "PENDING",
            Ticket.assignee_id.is_(None),
        ]
    elif scope == "mine":
        filters = [Ticket.assignee_id == tech_id]
    else:
        filters = [
            or_(
                and_(
                    Ticket.status == "PENDING",
                    Ticket.assignee_id.is_(None),
                ),
                Ticket.assignee_id == tech_id,
            )
        ]
    return await _paginate_tickets(
        session,
        filters,
        keyword=keyword,
        status=status,
        category=category,
        page=page,
        page_size=page_size,
    )


async def list_all_tickets(
    session: AsyncSession,
    *,
    keyword: str | None = None,
    status: str | None = None,
    category: str | None = None,
    page: int = 1,
    page_size: int = 10,
) -> tuple[list[tuple[Ticket, str, str | None]], int]:
    """管理员数据范围分页查询（LIST-001）：全部工单。"""
    return await _paginate_tickets(
        session,
        [],
        keyword=keyword,
        status=status,
        category=category,
        page=page,
        page_size=page_size,
    )


async def _paginate_tickets(
    session: AsyncSession,
    filters: list,
    *,
    keyword: str | None,
    status: str | None,
    category: str | None,
    page: int,
    page_size: int,
) -> tuple[list[tuple[Ticket, str, str | None]], int]:
    """共享的分页查询骨架：追加筛选、连表取姓名、updatedAt DESC、返回（行, 总数）。"""
    if status is not None:
        filters.append(Ticket.status == status)
    if category:
        filters.append(Ticket.category == category)
    if keyword:
        like = f"%{keyword}%"
        filters.append(
            or_(
                Ticket.ticket_no.ilike(like),
                Ticket.title.ilike(like),
                Ticket.location.ilike(like),
            )
        )

    assignee = aliased(User)
    stmt = (
        select(Ticket, User.display_name, assignee.display_name)
        .join(User, User.id == Ticket.reporter_id)
        .outerjoin(assignee, assignee.id == Ticket.assignee_id)
        .where(*filters)
        .order_by(Ticket.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = (await session.execute(stmt)).all()
    total = (
        await session.scalar(select(func.count(Ticket.id)).where(*filters)) or 0
    )
    return rows, total


async def count_tickets_by_reporter_status(
    session: AsyncSession, reporter_id: int
) -> dict[str, int]:
    """按状态统计学生本人工单数（DASH-001 口径基础）。"""
    rows = await session.execute(
        select(Ticket.status, func.count(Ticket.id))
        .where(Ticket.reporter_id == reporter_id)
        .group_by(Ticket.status)
    )
    return {status: count for status, count in rows.all()}


async def count_high_open_by_reporter(
    session: AsyncSession, reporter_id: int
) -> int:
    """统计 HIGH 优先级且未关闭/未取消的工单数（DASH-001 口径）。"""
    return (
        await session.scalar(
            select(func.count(Ticket.id)).where(
                Ticket.reporter_id == reporter_id,
                Ticket.priority == "HIGH",
                Ticket.status.not_in(("CLOSED", "CANCELLED")),
            )
        )
        or 0
    )


async def count_tickets_by_tech_status(
    session: AsyncSession, tech_id: int
) -> dict[str, int]:
    """按状态统计维修人员可见工单数（工单池 + 本人任务，DASH-001 口径）。"""
    rows = await session.execute(
        select(Ticket.status, func.count(Ticket.id))
        .where(
            or_(
                and_(
                    Ticket.status == "PENDING",
                    Ticket.assignee_id.is_(None),
                ),
                Ticket.assignee_id == tech_id,
            )
        )
        .group_by(Ticket.status)
    )
    return {status: count for status, count in rows.all()}


async def count_high_open_by_tech(session: AsyncSession, tech_id: int) -> int:
    """统计维修可见范围内 HIGH 且未关闭/未取消的工单数（DASH-001 口径）。"""
    return (
        await session.scalar(
            select(func.count(Ticket.id)).where(
                or_(
                    and_(
                        Ticket.status == "PENDING",
                        Ticket.assignee_id.is_(None),
                    ),
                    Ticket.assignee_id == tech_id,
                ),
                Ticket.priority == "HIGH",
                Ticket.status.not_in(("CLOSED", "CANCELLED")),
            )
        )
        or 0
    )


async def count_tickets_all_status(session: AsyncSession) -> dict[str, int]:
    """按状态统计全部工单数（管理员 DASH-001 口径）。"""
    rows = await session.execute(
        select(Ticket.status, func.count(Ticket.id)).group_by(Ticket.status)
    )
    return {status: count for status, count in rows.all()}


async def count_high_open_all(session: AsyncSession) -> int:
    """统计全部 HIGH 且未关闭/未取消的工单数（管理员 DASH-001 口径）。"""
    return (
        await session.scalar(
            select(func.count(Ticket.id)).where(
                Ticket.priority == "HIGH",
                Ticket.status.not_in(("CLOSED", "CANCELLED")),
            )
        )
        or 0
    )


async def get_ticket_with_names(
    session: AsyncSession, ticket_id: int
) -> tuple[Ticket, str, str | None] | None:
    """TKT-002：工单行 + 报修人姓名 + 负责人姓名（复用 LIST-001 的连表方式）。"""
    assignee = aliased(User)
    row = await session.execute(
        select(Ticket, User.display_name, assignee.display_name)
        .join(User, User.id == Ticket.reporter_id)
        .outerjoin(assignee, assignee.id == Ticket.assignee_id)
        .where(Ticket.id == ticket_id)
    )
    return row.first()


async def list_comments_with_author(
    session: AsyncSession, ticket_id: int
) -> list[tuple[TicketComment, str]]:
    """TKT-002/TKT-003：留言按时间正序（同一时间按 id 稳定排序），附带作者姓名。"""
    rows = await session.execute(
        select(TicketComment, User.display_name)
        .join(User, User.id == TicketComment.author_id)
        .where(TicketComment.ticket_id == ticket_id)
        .order_by(TicketComment.created_at.asc(), TicketComment.id.asc())
    )
    return rows.all()


async def list_logs_with_actor(
    session: AsyncSession, ticket_id: int
) -> list[tuple[TicketLog, str]]:
    """AUD-001：操作日志按时间正序（同一时间按 id 稳定排序），附带操作人姓名。"""
    rows = await session.execute(
        select(TicketLog, User.display_name)
        .join(User, User.id == TicketLog.actor_id)
        .where(TicketLog.ticket_id == ticket_id)
        .order_by(TicketLog.created_at.asc(), TicketLog.id.asc())
    )
    return rows.all()


async def create_comment(
    session: AsyncSession, ticket_id: int, author_id: int, content: str
) -> TicketComment:
    """TKT-003：新增留言行，flush 拿到自增 id（created_at 为库端默认，提交后需 refresh）。"""
    comment = TicketComment(
        ticket_id=ticket_id, author_id=author_id, content=content
    )
    session.add(comment)
    await session.flush()
    return comment


async def update_status_if(
    session: AsyncSession, ticket_id: int, expected_status: str, new_status: str
) -> bool:
    """FLOW-004：条件更新（id + 期望状态），返回是否命中行。

    并发下两个请求同时读同一状态时，只有一个 UPDATE 会命中，另一个返回 409。
    显式写 updated_at：Core UPDATE 不会触发 ORM 的 onupdate。
    """
    result = await session.execute(
        update(Ticket)
        .where(Ticket.id == ticket_id, Ticket.status == expected_status)
        .values(status=new_status, updated_at=func.now())
    )
    return result.rowcount > 0


async def accept_ticket_if(
    session: AsyncSession, ticket_id: int, tech_id: int
) -> bool:
    """FLOW-001：条件更新 PENDING 未指派 → PROCESSING 并指派本人（并发 409）。"""
    result = await session.execute(
        update(Ticket)
        .where(
            Ticket.id == ticket_id,
            Ticket.status == "PENDING",
            Ticket.assignee_id.is_(None),
        )
        .values(
            status="PROCESSING",
            assignee_id=tech_id,
            assigned_by=tech_id,
            assigned_at=func.now(),
            updated_at=func.now(),
        )
    )
    return result.rowcount > 0


async def resolve_ticket_if(
    session: AsyncSession, ticket_id: int, tech_id: int
) -> bool:
    """FLOW-003：条件更新（PROCESSING + 负责人=本人）→ RESOLVED（并发 409）。"""
    result = await session.execute(
        update(Ticket)
        .where(
            Ticket.id == ticket_id,
            Ticket.status == "PROCESSING",
            Ticket.assignee_id == tech_id,
        )
        .values(status="RESOLVED", updated_at=func.now())
    )
    return result.rowcount > 0


async def assign_ticket_if(
    session: AsyncSession, ticket_id: int, assignee_id: int, assigned_by: int
) -> bool:
    """FLOW-002：条件更新 PENDING 未指派 → PROCESSING，写入负责人/指派人/时间（并发 409）。"""
    result = await session.execute(
        update(Ticket)
        .where(
            Ticket.id == ticket_id,
            Ticket.status == "PENDING",
            Ticket.assignee_id.is_(None),
        )
        .values(
            status="PROCESSING",
            assignee_id=assignee_id,
            assigned_by=assigned_by,
            assigned_at=func.now(),
            updated_at=func.now(),
        )
    )
    return result.rowcount > 0
