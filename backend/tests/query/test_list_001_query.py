"""LIST-001 学生范围分页查询测试（S2，成员 B）。

覆盖：鉴权 401、学生数据范围、keyword（编号/标题/位置，不含描述）、
status/category 筛选、分页与默认 pageSize、updatedAt DESC 排序、参数校验 422。
"""

from datetime import timedelta

from tests.query.helpers import (
    BASE_TIME,
    add_tickets,
    auth_headers,
    make_ticket,
    user_id,
)


async def test_list_001_requires_login(seeded_client):
    client, _ = seeded_client
    resp = await client.get("/api/tickets")
    assert resp.status_code == 401
    assert resp.json()["code"] == 401


async def test_list_001_student_scope_only_own_tickets(seeded_client):
    client, Session = seeded_client
    student_id = await user_id(Session, "student")
    other_id = await user_id(Session, "student2")
    async with Session() as session:
        await add_tickets(
            session,
            make_ticket(student_id, ticket_no="REP-0001", title="投影仪故障"),
            make_ticket(student_id, ticket_no="REP-0002", title="网络掉线"),
            make_ticket(other_id, ticket_no="REP-0003", title="他人工单"),
        )

    headers = await auth_headers(client)
    resp = await client.get("/api/tickets", headers=headers)
    assert resp.status_code == 200
    body = resp.json()["data"]
    assert body["total"] == 2
    assert body["pages"] == 1
    assert body["page"] == 1
    assert body["pageSize"] == 10
    assert {item["ticketNo"] for item in body["items"]} == {"REP-0001", "REP-0002"}
    assert all(item["reporterId"] == student_id for item in body["items"])
    assert all(item["reporterName"] == "学生用户" for item in body["items"])


async def test_list_001_keyword_searches_ticket_no_title_location(seeded_client):
    client, Session = seeded_client
    student_id = await user_id(Session, "student")
    async with Session() as session:
        await add_tickets(
            session,
            make_ticket(
                student_id,
                ticket_no="REP-0001",
                title="投影仪无法显示",
                description="HDMI 无信号",
                location="实训楼 A-302",
            ),
            make_ticket(
                student_id,
                ticket_no="REP-0002",
                title="无线网络不稳定",
                description="晚间掉线",
                location="3 号宿舍楼 3F",
            ),
        )

    headers = await auth_headers(client)

    resp = await client.get(
        "/api/tickets", headers=headers, params={"keyword": "REP-0001"}
    )
    assert resp.json()["data"]["total"] == 1
    assert resp.json()["data"]["items"][0]["ticketNo"] == "REP-0001"

    resp = await client.get(
        "/api/tickets", headers=headers, params={"keyword": "投影仪"}
    )
    assert resp.json()["data"]["total"] == 1

    resp = await client.get(
        "/api/tickets", headers=headers, params={"keyword": "宿舍楼"}
    )
    assert resp.json()["data"]["total"] == 1
    assert resp.json()["data"]["items"][0]["ticketNo"] == "REP-0002"

    # keyword 只搜工单编号/标题/位置，不搜描述
    resp = await client.get(
        "/api/tickets", headers=headers, params={"keyword": "HDMI"}
    )
    assert resp.json()["data"]["total"] == 0


async def test_list_001_status_and_category_filters(seeded_client):
    client, Session = seeded_client
    student_id = await user_id(Session, "student")
    async with Session() as session:
        await add_tickets(
            session,
            make_ticket(student_id, ticket_no="REP-0001", status="PENDING"),
            make_ticket(
                student_id,
                ticket_no="REP-0002",
                status="RESOLVED",
                category="网络故障",
            ),
            make_ticket(
                student_id,
                ticket_no="REP-0003",
                status="PENDING",
                category="网络故障",
            ),
        )

    headers = await auth_headers(client)

    resp = await client.get(
        "/api/tickets", headers=headers, params={"status": "PENDING"}
    )
    assert resp.json()["data"]["total"] == 2

    resp = await client.get(
        "/api/tickets", headers=headers, params={"category": "网络故障"}
    )
    assert resp.json()["data"]["total"] == 2

    resp = await client.get(
        "/api/tickets",
        headers=headers,
        params={"status": "PENDING", "category": "网络故障"},
    )
    assert resp.json()["data"]["total"] == 1
    assert resp.json()["data"]["items"][0]["ticketNo"] == "REP-0003"


async def test_list_001_pagination_and_default_page_size(seeded_client):
    client, Session = seeded_client
    student_id = await user_id(Session, "student")
    async with Session() as session:
        await add_tickets(
            session,
            *[
                make_ticket(
                    student_id,
                    ticket_no=f"REP-{i:04d}",
                    title=f"测试工单 {i}",
                )
                for i in range(1, 26)
            ],
        )

    headers = await auth_headers(client)

    # 默认 pageSize=10
    resp = await client.get("/api/tickets", headers=headers)
    body = resp.json()["data"]
    assert body["total"] == 25
    assert body["pages"] == 3
    assert body["pageSize"] == 10
    assert len(body["items"]) == 10

    # 第二页
    resp = await client.get(
        "/api/tickets", headers=headers, params={"pageSize": 10, "page": 2}
    )
    body = resp.json()["data"]
    assert body["page"] == 2
    assert body["pages"] == 3
    assert len(body["items"]) == 10

    # 最后一页只剩 5 条
    resp = await client.get(
        "/api/tickets", headers=headers, params={"pageSize": 10, "page": 3}
    )
    assert len(resp.json()["data"]["items"]) == 5

    # 超出范围返回空列表但 total 不变
    resp = await client.get(
        "/api/tickets", headers=headers, params={"pageSize": 10, "page": 4}
    )
    body = resp.json()["data"]
    assert body["total"] == 25
    assert body["items"] == []


async def test_list_001_orders_by_updated_at_desc(seeded_client):
    client, Session = seeded_client
    student_id = await user_id(Session, "student")
    async with Session() as session:
        await add_tickets(
            session,
            make_ticket(
                student_id,
                ticket_no="REP-0001",
                updated_at=BASE_TIME + timedelta(hours=1),
            ),
            make_ticket(
                student_id,
                ticket_no="REP-0002",
                updated_at=BASE_TIME + timedelta(hours=3),
            ),
            make_ticket(
                student_id,
                ticket_no="REP-0003",
                updated_at=BASE_TIME + timedelta(hours=2),
            ),
        )

    headers = await auth_headers(client)
    resp = await client.get("/api/tickets", headers=headers)
    items = resp.json()["data"]["items"]
    assert [item["ticketNo"] for item in items] == ["REP-0002", "REP-0003", "REP-0001"]


async def test_list_001_rejects_invalid_page_and_page_size(seeded_client):
    client, Session = seeded_client
    headers = await auth_headers(client)

    resp = await client.get(
        "/api/tickets", headers=headers, params={"pageSize": 15}
    )
    assert resp.status_code == 422
    assert resp.json()["code"] == 422

    resp = await client.get("/api/tickets", headers=headers, params={"page": 0})
    assert resp.status_code == 422
    assert resp.json()["code"] == 422
