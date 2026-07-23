"""관리자 이메일 화이트리스트 등록 스크립트. 사용: python scripts/seed_admin.py <email> <name>

로그인은 구글/MS OAuth로 하므로 비밀번호는 없다 — 여기서는 "이 이메일은 관리자다"만 등록한다.
Alembic 마이그레이션은 스키마만 다루고 자격증명 시딩은 별도 스크립트로 분리한다(databases.md 원칙).
"""

import asyncio
import sys

sys.path.insert(0, ".")

from app.db.session import async_session_factory  # noqa: E402
from app.models.user import User  # noqa: E402


async def main(email: str, name: str) -> None:
    async with async_session_factory() as session:
        session.add(User(email=email, name=name))
        await session.commit()
    print(f"관리자 화이트리스트 등록 완료: {email}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("사용법: python scripts/seed_admin.py <email> <name>")
        sys.exit(1)
    asyncio.run(main(sys.argv[1], sys.argv[2]))
