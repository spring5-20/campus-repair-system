"""TKT-002 维修端详情/留言/日志可见性测试（BE2 轮次）。

覆盖：维修可见工单池与本人任务详情、他人任务 404（不泄露存在性）、
维修可留言/查看日志的可见范围。
"""

from tests.repair.helpers import add_tickets, auth_headers, make_ticket, user_id


async def _seed(client, Session):
    student_id = await user_id(Session, "student")
    tech_id = await user_id(Session, "tech")
    tech2_id = await user_id(Session, "tech2")
    async with Session() as session:
        pool = make_ticket(student_id, ticket_no="REP-0001", status="PENDING")
        mine = make_ticket(
            student_id,
            ticket_no="REP-0002",
            status="PROCESSING",
            assignee_id=tech_id,
        )
        other = make_ticket(
            student_id,
            ticket_no="REP-0003",
            status="PROCESSING",
            assignee_id=tech2_id,
        )
        session.add_all([pool, mine, other])
        await session.commit()
        await session.refresh(pool)
        await session.refresh(mine)
        await session.refresh(other)
        return pool.id, mine.id, other.id


async def test_tkt_002_tech_can_view_pool_and_own_tickets(seeded_client):
    client, Session = seeded_client
    pool_id, mine_id, _ = await _seed(client, Session)
    headers = await auth_headers(client, "tech")

    resp = await client.get(f"/api/tickets/{pool_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["assigneeName"] is None

    resp = await client.get(f"/api/tickets/{mine_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["assigneeName"] == "维修人员"


async def test_tkt_002_other_techs_ticket_is_404(seeded_client):
    """他人负责的工单对维修人员不可见，返回 404。"""
    client, Session = seeded_client
    _, _, other_id = await _seed(client, Session)
    headers = await auth_headers(client, "tech")
    resp = await client.get(f"/api/tickets/{other_id}", headers=headers)
    assert resp.status_code == 404
    assert resp.json()["code"] == 404


async def test_tkt_002_tech_comments_on_visible_ticket(seeded_client):
    client, Session = seeded_client
    pool_id, _, other_id = await _seed(client, Session)
    headers = await auth_headers(client, "tech")

    resp = await client.post(
        f"/api/tickets/{pool_id}/comments",
        headers=headers,
        json={"content": "收到，稍后到现场处理。"},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["authorName"] == "维修人员"
    assert data["content"] == "收到，稍后到现场处理。"

    # 留言写入 COMMENT 日志
    logs = (
        await client.get(f"/api/tickets/{pool_id}/logs", headers=headers)
    ).json()["data"]
    assert logs[-1]["action"] == "COMMENT"
    assert logs[-1]["actorName"] == "维修人员"

    # 他人任务不可留言，返回 404
    resp = await client.post(
        f"/api/tickets/{other_id}/comments",
        headers=headers,
        json={"content": "越权留言"},
    )
    assert resp.status_code == 404


async def test_tkt_002_tech_logs_visible_only_in_scope(seeded_client):
    client, Session = seeded_client
    pool_id, _, other_id = await _seed(client, Session)
    headers = await auth_headers(client, "tech")

    resp = await client.get(f"/api/tickets/{pool_id}/logs", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["data"] == []

    resp = await client.get(f"/api/tickets/{other_id}/logs", headers=headers)
    assert resp.status_code == 404
