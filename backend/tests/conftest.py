import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.core.security import hash_password
from app.main import app
from app.models.ticket import SequenceCounter
from app.models.user import User

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
DEMO_PASSWORD = "123456"


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as db:
        for username, display_name, role in (
            ("student", "学生用户", "student"),
            ("tech", "维修人员", "tech"),
            ("admin", "系统管理员", "admin"),
        ):
            db.add(
                User(
                    username=username,
                    display_name=display_name,
                    password_hash=hash_password(DEMO_PASSWORD),
                    role=role,
                )
            )
        db.add(SequenceCounter(name="ticket_no", value=0))
        await db.commit()
        yield db

    await engine.dispose()


@pytest_asyncio.fixture
async def client(session):
    async def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as c:
            yield c
    finally:
        app.dependency_overrides.clear()