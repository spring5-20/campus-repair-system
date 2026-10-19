"""TKT-003 处理留言测试（S3，成员 C）。

覆盖：鉴权 401、不存在/他人工单 404、留言成功返回 TicketComment、
纯空格/空内容 422 且不入库（AC-10）、首尾空格裁剪、COMMENT 日志写入。
"""

from sqlalchemy import func, select

from app.models.comment import TicketComment

from tests.interaction.helpers import auth_headers, make_ticket, user_id


async def _create_owned_ticket(client, Session, *, status: str = "PENDING") -> int:
    student_id = await user_id(Session, "student")
    async with Session() as session:
        ticket = make_ticket(student_id, ticket_no="REP-0001", status=status)
        session.add(ticket)
        await session.commit()
        await session.refresh(ticket)
        return ticket.id


async def test_tkt_003_requires_login(seeded_client):
    client, _ = seeded_client
    resp = await client.post("/api/tickets/1/comments", json={"content": "留言"})
    assert resp.status_code == 401


async def test_tkt_003_not_found_returns_404(seeded_client):
    client, _ = seeded_client
    headers = await auth_headers(client)
    resp = await client.post(
        "/api/tickets/999/comments", headers=headers, json={"content": "留言"}
    )
    assert resp.status_code == 404


async def test_tkt_003_other_students_ticket_is_404(seeded_client):
    client, Session = seeded_client
    other_id = await user_id(Session, "student2")
    async with Session() as session:
        ticket = make_ticket(other_id, ticket_no="REP-0001")
        session.add(ticket)
        await session.commit()
        await session.refresh(ticket)
    headers = await auth_headers(client)
    resp = await client.post(
        f"/api/tickets/{ticket.id}/comments", headers=headers, json={"content": "留言"}
    )
    assert resp.status_code == 404


async def test_tkt_003_add_comment_success(seeded_client):
    client, Session = seeded_client
    headers = await auth_headers(client)
    ticket_id = await _create_owned_ticket(client, Session)

    resp = await client.post(
        f"/api/tickets/{ticket_id}/comments",
        headers=headers,
        json={"content": "  请尽快处理，谢谢！  "},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["ticketId"] == ticket_id
    assert data["authorName"] == "学生用户"
    assert data["content"] == "请尽快处理，谢谢！"
    assert data["createdAt"]

    # 写 COMMENT 日志
    logs = (
        await client.get(f"/api/tickets/{ticket_id}/logs", headers=headers)
    ).json()["data"]
    assert logs[-1]["action"] == "COMMENT"
    assert logs[-1]["detail"] == "新增处理留言"
    assert logs[-1]["actorName"] == "学生用户"


async def test_tkt_003_pure_whitespace_is_422_and_not_stored(seeded_client):
    """AC-10：纯空格留言 422，留言不入库。"""
    client, Session = seeded_client
    headers = await auth_headers(client)
    ticket_id = await _create_owned_ticket(client, Session)

    resp = await client.post(
        f"/api/tickets/{ticket_id}/comments",
        headers=headers,
        json={"content": "   "},
    )
    assert resp.status_code == 422
    assert resp.json()["code"] == 422

    async with Session() as session:
        count = await session.scalar(
            select(func.count())
            .select_from(TicketComment)
            .where(TicketComment.ticket_id == ticket_id)
        )
    assert count == 0


async def test_tkt_003_empty_content_is_422(seeded_client):
    client, Session = seeded_client
    headers = await auth_headers(client)
    ticket_id = await _create_owned_ticket(client, Session)

    resp = await client.post(
        f"/api/tickets/{ticket_id}/comments", headers=headers, json={"content": ""}
    )
    assert resp.status_code == 422