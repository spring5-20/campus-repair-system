from datetime import datetime
from enum import Enum, StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel

from app.schemas.common import Page


class PageSize(int, Enum):
    """分页大小白名单：与契约 pageSize enum [10, 20, 50] 一致。"""

    TEN = 10
    TWENTY = 20
    FIFTY = 50


class TicketStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


class TicketPriority(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class TicketAction(StrEnum):
    ACCEPT = "ACCEPT"
    ASSIGN = "ASSIGN"
    RESOLVE = "RESOLVE"
    CLOSE = "CLOSE"
    CANCEL = "CANCEL"


class TicketScope(StrEnum):
    """列表范围筛选（LIST-001）：pool=工单池（PENDING 未指派），mine=指派给本人。"""

    POOL = "pool"
    MINE = "mine"


class TicketCreate(BaseModel):
    title: str = Field(min_length=3, max_length=80)
    description: str = Field(min_length=5, max_length=1000)
    category: str = Field(min_length=1, max_length=50)
    location: str = Field(min_length=2, max_length=100)
    priority: TicketPriority = TicketPriority.MEDIUM

    @field_validator("title", "description", "category", "location", mode="before")
    @classmethod
    def strip_whitespace(cls, value: object) -> object:
        """Strip before validation so pure-whitespace fields fail min_length (TKT-001)."""
        if isinstance(value, str):
            return value.strip()
        return value


class Ticket(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: int
    ticket_no: str
    title: str
    description: str
    category: str
    location: str
    priority: TicketPriority
    status: TicketStatus
    reporter_id: int
    reporter_name: str
    assignee_id: int | None
    assignee_name: str | None
    assigned_by: int | None
    assigned_at: datetime | None
    created_at: datetime
    updated_at: datetime


class TicketPage(Page[Ticket]):
    """分页响应 data 结构，名称与 docs/openapi.yaml 的 TicketPage 对齐。"""


class StatusChangeRequest(BaseModel):
    action: TicketAction


class AssigneeRequest(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    assignee_id: int


class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=500)

    @field_validator("content", mode="before")
    @classmethod
    def strip_whitespace(cls, value: object) -> object:
        """Strip before validation so pure-whitespace comments fail min_length (TKT-003, AC-10)."""
        if isinstance(value, str):
            return value.strip()
        return value


class TicketComment(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: int
    ticket_id: int
    author_id: int
    author_name: str
    content: str
    created_at: datetime


class TicketLog(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: int
    ticket_id: int
    actor_id: int
    actor_name: str
    action: str
    from_status: TicketStatus | None
    to_status: TicketStatus | None
    detail: str | None
    created_at: datetime


class TicketDetail(Ticket):
    """工单详情：基础信息 + 留言 + 操作时间线（TKT-002）。

    名称与 docs/openapi.yaml 的 TicketDetail 对齐（allOf Ticket + comments + logs）。
    """

    comments: list[TicketComment]
    logs: list[TicketLog]


class Statistics(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    total: int
    pending: int
    processing: int
    resolved: int
    closed: int
    cancelled: int
    high_open: int
    closure_rate: float
