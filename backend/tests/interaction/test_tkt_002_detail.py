"""TKT-002 工单详情测试（S3，成员 C）。

覆盖：鉴权 401、不存在/他人工单 404（数据范围）、
基础信息 + 负责人 + 留言 + 操作时间线、留言/日志按时间正序。
"""

from datetime import timedelta

from tests.interaction.helpers import (
    BASE_TIME,
    add_comment,
    add_log,
    auth_headers,
    make_ticket,
    user_id,
)


async def test_tkt_002_requires_login(seeded_client):
    client, _ = seeded_client
    resp = await client.get("/api/tickets/1")
    assert resp.status_code == 401
    assert resp.json()["code"] == 401


async def test_tkt_002_not_found_returns_404(seeded_client):
    client, _ = seeded_client
    headers = await auth_headers(client)
    resp = await client.get("/api/tickets/999", headers=headers)
    assert resp.status_code == 404
    assert resp.json()["code"] == 404


async def test_tkt_002_other_students_ticket_is_404(seeded_client):
    client, Session = seeded_client
    other_id = await user_id(Session, "student2")
    async with Session() as session:
        ticket = make_ticket(other_id, ticket_no="REP-0001", title="他人工单")
        session.add(ticket)
        await session.commit()
        await session.refresh(ticket)
    headers = await auth_headers(client)
    resp = await client.get(f"/api/tickets/{ticket.id}", headers=headers)
    assert resp.status_code == 404


async def test_tkt_002_detail_includes_comments_and_logs(seeded_client):
    client, Session = seeded_client
    student_id = await user_id(Session, "student")
    tech_id = await user_id(Session, "tech")
    async with Session() as session:
        ticket = make_ticket(
            student_id,
            ticket_no="REP-0001",
            title="投影仪无法显示",
            assignee_id=tech_id,
        )
        session.add(ticket)
        await session.commit()
        await session.refresh(ticket)
        await add_log(
            session,
            ticket_id=ticket.id,
            actor_id=student_id,
            action="CREATE",
            to_status="PENDING",
            detail="提交报修申请",
        )
        await add_log(
            session,
            ticket_id=ticket.id,
            actor_id=student_id,
            action="COMMENT",
            detail="新增处理留言",
        )
        await add_comment(
            session,
            ticket_id=ticket.id,
            author_id=student_id,
            content="请尽快处理",
        )

    headers = await auth_headers(client)
    resp = await client.get(f"/api/tickets/{ticket.id}", headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    # 基础信息
    assert data["ticketNo"] == "REP-0001"
    assert data["title"] == "投影仪无法显示"
    assert data["status"] == "PENDING"
    assert data["reporterName"] == "学生用户"
    assert data["assigneeName"] == "维修人员"
    # 留言
    assert len(data["comments"]) == 1
    comment = data["comments"][0]
    assert comment["content"] == "请尽快处理"
    assert comment["authorName"] == "学生用户"
    assert comment["ticketId"] == ticket.id
    # 日志时间线
    assert [log["action"] for log in data["logs"]] == ["CREATE", "COMMENT"]


async def test_tkt_002_comments_ordered_by_time_asc(seeded_client):
    client, Session = seeded_client
    student_id = await user_id(Session, "student")
    async with Session() as session:
        ticket = make_ticket(student_id, ticket_no="REP-0001")
        session.add(ticket)
        await session.commit()
        await session.refresh(ticket)
        await add_comment(
            session,
            ticket_id=ticket.id,
            author_id=student_id,
            content="第一条",
            created_at=BASE_TIME + timedelta(hours=1),
        )
        await add_comment(
            session,
            ticket_id=ticket.id,
            author_id=student_id,
            content="第二条",
            created_at=BASE_TIME + timedelta(hours=2),
        )
        await add_comment(
            session,
            ticket_id=ticket.id,
            author_id=student_id,
            content="第三条",
            created_at=BASE_TIME + timedelta(hours=3),
        )

    headers = await auth_headers(client)
    data = (
        await client.get(f"/api/tickets/{ticket.id}", headers=headers)
    ).json()["data"]
    assert [c["content"] for c in data["comments"]] == ["第一条", "第二条", "第三条"]


async def test_tkt_002_logs_ordered_by_time_asc(seeded_client):
    client, Session = seeded_client
    student_id = await user_id(Session, "student")
    tech_id = await user_id(Session, "tech")
    async with Session() as session:
        ticket = make_ticket(student_id, ticket_no="REP-0001")
        session.add(ticket)
        await session.commit()
        await session.refresh(ticket)
        await add_log(
            session,
            ticket_id=ticket.id,
            actor_id=student_id,
            action="CREATE",
            to_status="PENDING",
            detail="提交报修申请",
            created_at=BASE_TIME + timedelta(hours=1),
        )
        await add_log(
            session,
            ticket_id=ticket.id,
            actor_id=student_id,
            action="COMMENT",
            detail="新增处理留言",
            created_at=BASE_TIME + timedelta(hours=2),
        )
        await add_log(
            session,
            ticket_id=ticket.id,
            actor_id=tech_id,
            action="RESOLVE",
            from_status="PROCESSING",
            to_status="RESOLVED",
            detail="完成维修",
            created_at=BASE_TIME + timedelta(hours=3),
        )

    headers = await auth_headers(client)
    data = (
        await client.get(f"/api/tickets/{ticket.id}", headers=headers)
    ).json()["data"]
    logs = data["logs"]
    assert [log["action"] for log in logs] == ["CREATE", "COMMENT", "RESOLVE"]
    assert logs[0]["fromStatus"] is None
    assert logs[1]["fromStatus"] is None
    assert logs[2]["fromStatus"] == "PROCESSING"
    assert logs[2]["toStatus"] == "RESOLVED"
    assert logs[0]["createdAt"] <= logs[2]["createdAt"]


async def test_tkt_002_empty_comments_and_logs_lists(seeded_client):
    client, Session = seeded_client
    student_id = await user_id(Session, "student")
    async with Session() as session:
        ticket = make_ticket(student_id, ticket_no="REP-0001")
        session.add(ticket)
        await session.commit()
        await session.refresh(ticket)
    headers = await auth_headers(client)
    data = (
        await client.get(f"/api/tickets/{ticket.id}", headers=headers)
    ).json()["data"]
    assert data["comments"] == []
    assert data["logs"] == []