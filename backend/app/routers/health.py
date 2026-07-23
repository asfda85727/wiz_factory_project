"""헬스체크. DB 연결 실패도 500이 아니라 200 + degraded 표시로 안전하게 반환한다
(로컬에서 DB 없이도 라우팅 자체를 확인할 수 있도록 하는 의도적 설계)."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db_session)) -> dict:
    try:
        await db.execute(text("SELECT 1"))
        db_status = "ok"
    except SQLAlchemyError:
        db_status = "unavailable"
    return {"status": "ok", "database": db_status}
