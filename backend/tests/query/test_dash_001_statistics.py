"""DASH-001 学生统计口径测试（S2，成员 B）。

口径：与列表数据范围一致（只统计本人）；highOpen = HIGH 且非 CLOSED/CANCELLED；
closureRate = closed / 全部可见工单（含 cancelled），取整百分比。
"""

from tests.query.helpers import add_tickets, auth_headers, make_ticket, user_id


async def test_dash_001_requires_login(seeded_client):
    client, _ = seeded_client
    resp = await client.get("/api/tickets/statistics")
    assert resp.status_code == 401
    assert resp.json()["code"] == 401


async def test_dash_001_student_scope_and_counts(seeded_client):
    client, Session = seeded_client
    student_id = await user_id(Session, "student")
    other_id = await user_id(Session, "student2")
    async with Session() as session:
        await add_tickets(
            session,
            # student 本人：PENDING x2（其一 HIGH）、PROCESSING、RESOLVED、CLOSED(HIGH)、CANCELLED
            make_ticket(student_id, ticket_no="REP-0001", status="PENDING"),
            make_ticket(
                student_id,
                ticket_no="REP-0002",
                status="PENDING",
                priority="HIGH",
            ),
            make_ticket(student_id, ticket_no="REP-0003", status="PROCESSING"),
            make_ticket(
                student_id,
                ticket_no="REP-0004",
                status="RESOLVED",
                priority="LOW",
            ),
            make_ticket(
                student_id,
                ticket_no="REP-0005",
                status="CLOSED",
                priority="HIGH",
            ),
            make_ticket(student_id, ticket_no="REP-0006", status="CANCELLED"),
            # student2 的工单不计入 student 统计
            make_ticket(
                other_id,
                ticket_no="REP-0101",
                status="CLOSED",
                priority="HIGH",
            ),
        )

    headers = await auth_headers(client)
    resp = await client.get("/api/tickets/statistics", headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["total"] == 6
    assert data["pending"] == 2
    assert data["processing"] == 1
    assert data["resolved"] == 1
    assert data["closed"] == 1
    assert data["cancelled"] == 1
    # highOpen：HIGH 且未关闭/未取消，只有 REP-0002；REP-0005 已关闭不计
    assert data["highOpen"] == 1
    # closureRate = round(1 / 6 * 100) = 17
    assert data["closureRate"] == 17


async def test_dash_001_empty_scope_returns_zero_counts(seeded_client):
    client, Session = seeded_client
    headers = await auth_headers(client)
    resp = await client.get("/api/tickets/statistics", headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data == {
        "total": 0,
        "pending": 0,
        "processing": 0,
        "resolved": 0,
        "closed": 0,
        "cancelled": 0,
        "highOpen": 0,
        "closureRate": 0.0,
    }


async def test_dash_001_closure_rate_includes_cancelled_in_denominator(seeded_client):
    client, Session = seeded_client
    student_id = await user_id(Session, "student")
    async with Session() as session:
        await add_tickets(
            session,
            make_ticket(student_id, ticket_no="REP-0001", status="CLOSED"),
            make_ticket(student_id, ticket_no="REP-0002", status="CANCELLED"),
        )

    headers = await auth_headers(client)
    data = (
        await client.get("/api/tickets/statistics", headers=headers)
    ).json()["data"]
    assert data["total"] == 2
    assert data["closed"] == 1
    assert data["cancelled"] == 1
    assert data["closureRate"] == 50


async def test_dash_001_high_open_excludes_cancelled(seeded_client):
    client, Session = seeded_client
    student_id = await user_id(Session, "student")
    async with Session() as session:
        await add_tickets(
            session,
            make_ticket(
                student_id,
                ticket_no="REP-0001",
                status="CANCELLED",
                priority="HIGH",
            ),
        )

    headers = await auth_headers(client)
    data = (
        await client.get("/api/tickets/statistics", headers=headers)
    ).json()["data"]
    assert data["total"] == 1
    assert data["highOpen"] == 0
