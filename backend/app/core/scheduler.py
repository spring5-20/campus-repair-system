"""后台定时任务：超时未确认的工单自动确认完成（FLOW-004 自动化）。

每天固定时刻扫描 RESOLVED 状态滞留超过配置时长的工单，系统代为执行
CLOSE（确认完成）。调度器随 FastAPI lifespan 启动/停止；测试环境经
httpx.ASGITransport 不触发 lifespan，故 cron 不会在测试中运行。
"""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import get_settings
from app.core.database import SessionFactory
from app.services.ticket_service import auto_close_stale_resolved

settings = get_settings()
logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


async def auto_close_stale_tickets_job() -> None:
    """cron 任务体：打开独立会话执行自动关闭，结果仅记日志。"""
    async with SessionFactory() as session:
        closed = await auto_close_stale_resolved(
            session, timeout_hours=settings.auto_close_timeout_hours
        )
    if closed:
        logger.info("Auto-closed %d stale ticket(s)", closed)


def start_scheduler() -> None:
    """启动后台调度器（FastAPI lifespan 起）。若配置禁用则忽略。"""
    global _scheduler
    if not settings.scheduler_enabled or _scheduler is not None:
        return
    _scheduler = AsyncIOScheduler(timezone=settings.scheduler_timezone)
    _scheduler.add_job(
        auto_close_stale_tickets_job,
        CronTrigger(
            hour=settings.auto_close_cron_hour,
            minute=settings.auto_close_cron_minute,
            timezone=settings.scheduler_timezone,
        ),
        id="auto-close-stale-tickets",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info(
        "Scheduler started: daily %02d:%02d auto-close stale tickets",
        settings.auto_close_cron_hour,
        settings.auto_close_cron_minute,
    )


def shutdown_scheduler() -> None:
    """停止后台调度器（FastAPI lifespan 关）。"""
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
