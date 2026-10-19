"""DASH-001 维修/管理员统计口径测试（BE2 轮次）。

口径：与各自列表数据范围一致；highOpen=HIGH 且未关闭/未取消；
closureRate=closed / 全部可见工单（含 cancelled），取整百分比。
"""

from tests.repair.helpers import add_tickets, auth_headers, make_ticket, user_id


async def test_dash_001_tech_scope_statistics(seeded_client):
    client, Session = seeded_client
    student_id = await user_id(Session, "student")
    tech_id = await user_id(Session, "tech")
    tech2_id = await user_id(Session, "tech2")
    async with Session() as session:
        await add_tickets(
            session,
            # 工单池（PENDING 未指派）
            make_ticket(student_id, ticket_no="REP-0001", status="PENDING"),
            make_ticket(
                student_id,
                ticket_no="REP-0002",
                status="PENDING",
                priority="HIGH",
            ),
            # 本人任务
            make_ticket(
                student_id,
                ticket_no="REP-0003",
                status="PROCESSING",
                assignee_id=tech_id,
            ),
            make_ticket(
                student_id,
                ticket_no="REP-0004",
                status="RESOLVED",
                priority="LOW",
                assignee_id=tech_id,
            ),
            make_ticket(
                student_id,
                ticket_no="REP-0005",
                status="CLOSED",
                priority="HIGH",
                assignee_id=tech_id,
            ),
            # 他人任务与取消工单不计入维修统计
            make_ticket(
                student_id,
                ticket_no="REP-0006",
                status="PROCESSING",
                priority="HIGH",
                assignee_id=tech2_id,
            ),
            make_ticket(student_id, ticket_no="REP-0007", status="CANCELLED"),
        )

    headers = await auth_headers(client, "tech")
    resp = await client.get("/api/tickets/statistics", headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["total"] == 5
    assert data["pending"] == 2
    assert data["processing"] == 1
    assert data["resolved"] == 1
    assert data["closed"] == 1
    assert data["cancelled"] == 0
    # highOpen：REP-0002（工单池 HIGH PENDING）；REP-0005 已关闭不计
    assert data["highOpen"] == 1
    # closureRate = round(1 / 5 * 100) = 20
    assert data["closureRate"] == 20


async def test_dash_001_admin_sees_all_tickets(seeded_client):
    client, Session = seeded_client
    student_id = await user_id(Session, "student")
    tech_id = await user_id(Session, "tech")
    tech2_id = await user_id(Session, "tech2")
    async with Session() as session:
        await add_tickets(
            session,
            make_ticket(student_id, ticket_no="REP-0001", status="PENDING"),
            make_ticket(
                student_id,
                ticket_no="REP-0002",
                status="PENDING",
                priority="HIGH",
            ),
            make_ticket(
                student_id,
                ticket_no="REP-0003",
                status="PROCESSING",
                assignee_id=tech_id,
            ),
            make_ticket(
                student_id,
                ticket_no="REP-0004",
                status="RESOLVED",
                assignee_id=tech_id,
            ),
            make_ticket(
                student_id,
                ticket_no="REP-0005",
                status="CLOSED",
                priority="HIGH",
                assignee_id=tech_id,
            ),
            make_ticket(
                student_id,
                ticket_no="REP-0006",
                status="PROCESSING",
                priority="HIGH",
                assignee_id=tech2_id,
            ),
            make_ticket(student_id, ticket_no="REP-0007", status="CANCELLED"),
        )

    headers = await auth_headers(client, "admin")
    data = (
        await client.get("/api/tickets/statistics", headers=headers)
    ).json()["data"]
    assert data["total"] == 7
    assert data["pending"] == 2
    assert data["processing"] == 2
    assert data["resolved"] == 1
    assert data["closed"] == 1
    assert data["cancelled"] == 1
    assert data["highOpen"] == 2
    # closureRate = round(1 / 7 * 100) = 14
    assert data["closureRate"] == 14
