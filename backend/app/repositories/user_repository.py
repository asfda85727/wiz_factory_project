"""관리자 계정 조회. 이메일 화이트리스트 조회만 한다(로그인 자체는 구글/MS OAuth)."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()
