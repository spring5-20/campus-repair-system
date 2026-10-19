"""LIST-001 维修/管理员数据范围与筛选测试（BE2 轮次）。

覆盖：维修可见范围=工单池（PENDING 未指派）+ 本人任务、scope=pool/mine、
status/category/keyword 筛选、scope 参数校验 422、管理员全量可见。
"""

from tests.repair.helpers import add_tickets, auth_headers, make_ticket, user_id


async def _seed_scope_tickets(client, Session):
    student_id = await user_id(Session, "student")
    tech_id = await user_id(Session, "tech")
    tech2_id = await user_id(Session, "tech2")
    async with Session() as session:
        await add_tickets(
            session,
            make_ticket(student_id, ticket_no="REP-0001", status="PENDING"),
            make_ticket(
                student_id, ticket_no="REP-0002", status="PENDING", assignee_id=tech_id
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
                status="PROCESSING",
                assignee_id=tech2_id,
            ),
            make_ticket(
                student_id,
                ticket_no="REP-0005",
                status="RESOLVED",
                assignee_id=tech_id,
            ),
            make_ticket(
                student_id,
                ticket_no="REP-0006",
                status="CLOSED",
                assignee_id=tech2_id,
            ),
        )


async def test_list_001_tech_scope_pool_and_mine(seeded_client):
    """维修默认可见=工单池+本人任务；scope=pool/mine 进一步收窄。"""
    client, Session = seeded_client
    await _seed_scope_tickets(client, Session)

    headers = await auth_headers(client, "tech")
    resp = await client.get("/api/tickets", headers=headers)
    assert resp.status_code == 200
    body = resp.json()["data"]
    assert body["total"] == 4
    assert {item["ticketNo"] for item in body["items"]} == {
        "REP-0001",
        "REP-0002",
        "REP-0003",
        "REP-0005",
    }

    resp = await client.get("/api/tickets", headers=headers, params={"scope": "pool"})
    body = resp.json()["data"]
    assert body["total"] == 1
    assert body["items"][0]["ticketNo"] == "REP-0001"

    resp = await client.get("/api/tickets", headers=headers, params={"scope": "mine"})
    body = resp.json()["data"]
    assert body["total"] == 3
    assert {item["ticketNo"] for item in body["items"]} == {
        "REP-0002",
        "REP-0003",
        "REP-0005",
    }


async def test_list_001_tech_filters_within_scope(seeded_client):
    """status/category/keyword 筛选在维修数据范围内生效。"""
    client, Session = seeded_client
    student_id = await user_id(Session, "student")
    tech_id = await user_id(Session, "tech")
    async with Session() as session:
        await add_tickets(
            session,
            make_ticket(
                student_id,
                ticket_no="REP-0001",
                status="PENDING",
                category="教学设备",
                location="实训楼 A-302",
            ),
            make_ticket(
                student_id,
                ticket_no="REP-0002",
                status="PENDING",
                category="网络故障",
                location="3 号宿舍楼 3F",
            ),
            make_ticket(
                student_id,
                ticket_no="REP-0003",
                status="PROCESSING",
                category="网络故障",
                assignee_id=tech_id,
            ),
        )

    headers = await auth_headers(client, "tech")

    resp = await client.get(
        "/api/tickets", headers=headers, params={"status": "PENDING"}
    )
    assert resp.json()["data"]["total"] == 2

    resp = await client.get(
        "/api/tickets", headers=headers, params={"category": "网络故障"}
    )
    body = resp.json()["data"]
    assert body["total"] == 2
    assert {item["ticketNo"] for item in body["items"]} == {"REP-0002", "REP-0003"}

    resp = await client.get(
        "/api/tickets", headers=headers, params={"keyword": "REP-0003"}
    )
    assert resp.json()["data"]["total"] == 1

    resp = await client.get(
        "/api/tickets",
        headers=headers,
        params={"status": "PENDING", "category": "网络故障"},
    )
    assert resp.json()["data"]["total"] == 1


async def test_list_001_invalid_scope_returns_422(seeded_client):
    client, Session = seeded_client
    headers = await auth_headers(client, "tech")
    resp = await client.get("/api/tickets", headers=headers, params={"scope": "other"})
    assert resp.status_code == 422
    assert resp.json()["code"] == 422


async def test_list_001_admin_sees_all_tickets(seeded_client):
    client, Session = seeded_client
    await _seed_scope_tickets(client, Session)

    headers = await auth_headers(client, "admin")
    resp = await client.get("/api/tickets", headers=headers)
    assert resp.status_code == 200
    body = resp.json()["data"]
    assert body["total"] == 6
    assert len(body["items"]) == 6


async def test_list_001_student_scope_unaffected_by_scope_param(seeded_client):
    """学生列表始终只返回本人数据，scope 参数对其不生效。"""
    client, Session = seeded_client
    student_id = await user_id(Session, "student")
    tech_id = await user_id(Session, "tech")
    async with Session() as session:
        await add_tickets(
            session,
            make_ticket(student_id, ticket_no="REP-0001", status="PENDING"),
            make_ticket(
                student_id,
                ticket_no="REP-0002",
                status="PROCESSING",
                assignee_id=tech_id,
            ),
        )

    headers = await auth_headers(client, "student")
    resp = await client.get("/api/tickets", headers=headers, params={"scope": "pool"})
    assert resp.status_code == 200
    assert resp.json()["data"]["total"] == 2
