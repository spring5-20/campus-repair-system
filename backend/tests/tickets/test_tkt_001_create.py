import pytest
from sqlalchemy import delete, select

from app.models.log import TicketLog
from app.models.ticket import SequenceCounter


async def _login(client, username="student", password="123456"):
    resp = await client.post(
        "/api/auth/login", json={"username": username, "password": password}
    )
    assert resp.status_code == 200
    return resp.json()["data"]["token"]


async def _create(client, token, **overrides):
    payload = {
        "title": "宿舍空调不制冷",
        "description": "空调开启后出风口只有自然风，无法制冷，已持续两天。",
        "category": "水电设施",
        "location": "3 号宿舍楼 402",
        "priority": "HIGH",
    }
    payload.update(overrides)
    return await client.post(
        "/api/tickets", json=payload, headers={"Authorization": f"Bearer {token}"}
    )


async def test_tkt_001_create_ticket_success(client):
    token = await _login(client)
    resp = await _create(client, token)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    data = body["data"]
    assert data["ticketNo"] == "REP-0001"
    assert data["status"] == "PENDING"
    assert data["priority"] == "HIGH"
    assert data["reporterName"] == "学生用户"
    assert data["reporterId"] is not None
    assert data["assigneeId"] is None
    assert data["assigneeName"] is None
    assert data["createdAt"]
    assert data["updatedAt"]


async def test_tkt_001_create_default_priority_medium(client):
    token = await _login(client)
    resp = await client.post(
        "/api/tickets",
        json={
            "title": "教室灯管损坏",
            "description": "靠窗第三排灯管闪烁，需要更换。",
            "category": "教学设备",
            "location": "教学楼 A-101",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["priority"] == "MEDIUM"


async def test_tkt_001_create_increments_ticket_no(client):
    token = await _login(client)
    first = await _create(client, token)
    second = await _create(client, token)
    first_no = first.json()["data"]["ticketNo"]
    second_no = second.json()["data"]["ticketNo"]
    assert first_no == "REP-0001"
    assert second_no == "REP-0002"
    assert first_no != second_no


async def test_tkt_001_create_writes_create_log(client, session):
    token = await _login(client)
    resp = await _create(client, token)
    ticket_id = resp.json()["data"]["id"]
    log = await session.scalar(
        select(TicketLog).where(TicketLog.ticket_id == ticket_id)
    )
    assert log is not None
    assert log.action == "CREATE"
    assert log.from_status is None
    assert log.to_status == "PENDING"
    assert log.detail == "提交报修申请"


@pytest.mark.parametrize("username", ["tech", "admin"])
async def test_tkt_001_create_forbidden_for_non_student(client, username):
    token = await _login(client, username=username)
    resp = await _create(client, token)
    assert resp.status_code == 403
    assert resp.json()["code"] == 403


async def test_tkt_001_create_requires_auth(client):
    resp = await _create(client, "not-a-token")
    assert resp.status_code == 401
    assert resp.json()["code"] == 401


async def test_tkt_001_create_validation_422(client):
    token = await _login(client)
    resp = await _create(client, token, title="ab", description="short", location="x")
    assert resp.status_code == 422
    assert resp.json()["code"] == 422


async def test_tkt_001_create_missing_fields_422(client):
    token = await _login(client)
    resp = await client.post(
        "/api/tickets",
        json={"title": "缺字段"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422
    assert resp.json()["code"] == 422


@pytest.mark.parametrize("field", ["title", "description", "location", "category"])
async def test_tkt_001_create_pure_whitespace_422(client, field):
    token = await _login(client)
    resp = await _create(client, token, **{field: "   "})
    assert resp.status_code == 422
    assert resp.json()["code"] == 422


async def test_tkt_001_create_initializes_counter_if_missing(client, session):
    await session.execute(delete(SequenceCounter))
    await session.commit()
    token = await _login(client)
    resp = await _create(client, token)
    assert resp.status_code == 200
    assert resp.json()["data"]["ticketNo"] == "REP-0001"