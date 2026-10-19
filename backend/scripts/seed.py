"""Idempotent seed: demo accounts + sample tickets mirroring the prototype."""

import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.core.database import Base
from app.core.security import hash_password
from app.models.comment import TicketComment
from app.models.log import TicketLog
from app.models.ticket import SequenceCounter, Ticket
from app.models.user import User


DEMO_PASSWORD = "123456"


async def seed() -> None:
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as session:
        # Accounts: student / tech / admin
        accounts = [
            ("student", "学生用户", "student"),
            ("tech", "维修人员", "tech"),
            ("admin", "系统管理员", "admin"),
        ]
        users = {}
        for username, display_name, role in accounts:
            existing = await session.scalar(select(User).where(User.username == username))
            if existing:
                users[username] = existing
                continue
            user = User(
                username=username,
                display_name=display_name,
                password_hash=hash_password(DEMO_PASSWORD),
                role=role,
            )
            session.add(user)
            await session.flush()
            users[username] = user

        # Sample tickets (ticketNo REP-0001..REP-0007) mirroring the prototype.
        now = datetime.now(timezone.utc)
        samples = [
            ("REP-0001", "实训室投影仪无法显示", "电脑已连接 HDMI，投影仪仍提示无信号，请协助检查线路和信号源。", "教学设备", "实训楼 A-302", "HIGH", "PENDING", None, None),
            ("REP-0002", "宿舍楼三层无线网络不稳定", "晚间频繁掉线，多个房间均有相同情况，希望检查楼层 AP 信号。", "网络故障", "3 号宿舍楼 3F", "MEDIUM", "PROCESSING", "tech", None),
            ("REP-0003", "图书馆二楼饮水机漏水", "饮水机底部持续有少量积水，现场已放置警示牌，请尽快处理。", "水电设施", "图书馆 2F 东侧", "HIGH", "RESOLVED", "tech", None),
            ("REP-0004", "教学楼一楼照明灯闪烁", "走廊东侧第二盏灯频繁闪烁，影响晚间通行。", "水电设施", "教学楼 B-1F", "LOW", "CLOSED", "tech", None),
            ("REP-0005", "机房 12 号电脑无法启动", "按下电源键后没有反应，已检查插座正常。", "电脑设备", "实训楼 C-401", "MEDIUM", "PENDING", None, None),
            ("REP-0006", "多媒体讲台 USB 接口松动", "U 盘插入后经常断开连接，建议检查接口。", "教学设备", "教学楼 A-105", "LOW", "CANCELLED", None, None),
            ("REP-0007", "宿舍洗手间水龙头无法关闭", "水龙头阀门损坏，一直有细水流出。", "水电设施", "2 号宿舍楼 4F", "HIGH", "PROCESSING", "tech", None),
        ]
        for no, title, description, category, location, priority, status, assignee, _assigned_at in samples:
            existing = await session.scalar(select(Ticket).where(Ticket.ticket_no == no))
            if existing:
                continue
            ticket = Ticket(
                ticket_no=no,
                title=title,
                description=description,
                category=category,
                location=location,
                priority=priority,
                status=status,
                reporter_id=users["student"].id,
                assignee_id=users[assignee].id if assignee else None,
                assigned_by=users["admin"].id if assignee else None,
                assigned_at=now - timedelta(days=1) if assignee else None,
                created_at=now - timedelta(days=2),
                updated_at=now - timedelta(days=1),
            )
            session.add(ticket)
            await session.flush()
            session.add(
                TicketLog(
                    ticket_id=ticket.id,
                    actor_id=users["student"].id,
                    action="CREATE",
                    from_status=None,
                    to_status="PENDING",
                    detail="提交报修申请",
                )
            )
            if status == "PROCESSING":
                action = "ASSIGN" if no == "REP-0007" else "ACCEPT"
                session.add(
                    TicketLog(
                        ticket_id=ticket.id,
                        actor_id=users[assignee].id,
                        action=action,
                        from_status="PENDING",
                        to_status="PROCESSING",
                        detail="接单/指派",
                    )
                )
            if status == "RESOLVED":
                session.add(
                    TicketLog(
                        ticket_id=ticket.id,
                        actor_id=users["tech"].id,
                        action="RESOLVE",
                        from_status="PROCESSING",
                        to_status="RESOLVED",
                        detail="完成维修",
                    )
                )
            if status == "CLOSED":
                session.add(
                    TicketComment(
                        ticket_id=ticket.id,
                        author_id=users["tech"].id,
                        content="已更换设备并复测正常，请确认。",
                    )
                )
            if status == "CANCELLED":
                session.add(
                    TicketLog(
                        ticket_id=ticket.id,
                        actor_id=users["student"].id,
                        action="CANCEL",
                        from_status="PENDING",
                        to_status="CANCELLED",
                        detail="学生取消工单",
                    )
                )

        if await session.scalar(
            select(SequenceCounter).where(SequenceCounter.name == "ticket_no")
        ) is None:
            max_no = max(int(no.split("-")[1]) for no, *_ in samples)
            session.add(SequenceCounter(name="ticket_no", value=max_no))

        await session.commit()

    await engine.dispose()
    print("Seed complete: student/tech/admin (password 123456) + REP-0001..REP-0007")


if __name__ == "__main__":
    asyncio.run(seed())
