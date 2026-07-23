"""테스트 공용 픽스처. 로컬 docker-compose Postgres에 연결하되, 각 테스트를 트랜잭션 롤백으로 격리한다."""

from datetime import date

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import engine
from app.models.site import Site
from app.models.user import User


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine_after_test():
    # 테스트마다 새 이벤트 루프가 생기는데(pytest-asyncio 기본 function scope), asyncpg 커넥션은
    # 자신을 만든 이벤트 루프에 묶여 있어 풀링된 커넥션을 다음 테스트에서 재사용하면 Windows
    # ProactorEventLoop에서 깨진다. 매 테스트 후 풀을 비워 다음 테스트가 새 커넥션을 맺게 한다.
    yield
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session():
    async with engine.connect() as connection:
        async with connection.begin() as transaction:
            session = AsyncSession(bind=connection, expire_on_commit=False)
            try:
                yield session
            finally:
                await session.close()
                await transaction.rollback()


@pytest_asyncio.fixture
async def actor_id(db_session: AsyncSession):
    user = User(email="pytest-actor@example.com", name="테스트 관리자")
    db_session.add(user)
    await db_session.flush()
    return user.id


@pytest_asyncio.fixture
async def site_id(db_session: AsyncSession):
    site = Site(name="테스트 현장", client_name="테스트 원청", start_date=date(2026, 1, 1))
    db_session.add(site)
    await db_session.flush()
    return site.id


@pytest_asyncio.fixture
async def other_site_id(db_session: AsyncSession):
    site = Site(name="다른 현장", client_name="다른 원청", start_date=date(2026, 2, 1))
    db_session.add(site)
    await db_session.flush()
    return site.id
