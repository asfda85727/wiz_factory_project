"""비동기 DB 엔진과 세션 팩토리. FastAPI Depends에서 세션을 주입받는 용도."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings


# 로컬 개발 환경의 홈 디렉터리 경로에 비ASCII 문자가 포함되어 있으면 asyncpg가 기본 sslmode
# 탐색(클라이언트 인증서 경로 프로빙) 과정에서 OSError(Illegal byte sequence)를 던진다.
# 사설망 내부 DB 연결이라 SSL이 필요 없으므로 명시적으로 비활성화한다.
engine = create_async_engine(settings.database_url, pool_pre_ping=True, connect_args={"ssl": False})
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session
