"""维修端切片本地测试夹具：内存库 + 演示账号（含第二维修人员 tech2）。"""

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.core.security import hash_password
from app.main import app
from app.models.user import User

DEMO_PASSWORD = "123456"


@pytest_asyncio.fixture
async def seeded_client():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as session:
        for username, display_name, role in (
            ("student", "学生用户", "student"),
            ("student2", "学生二号", "student"),
            ("tech", "维修人员", "tech"),
            ("tech2", "维修二号", "tech"),
            ("admin", "系统管理员", "admin"),
        ):
            session.add(
                User(
                    username=username,
                    display_name=display_name,
                    password_hash=hash_password(DEMO_PASSWORD),
                    role=role,
                )
            )
        await session.commit()

    async def override_get_db():
        async with Session() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            yield client, Session
    finally:
        app.dependency_overrides.clear()
        await engine.dispose()
