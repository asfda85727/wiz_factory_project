"""검증 에러(422)가 영어 원문("Field required" 등) 대신 한글 메시지로 내려가는지 확인."""

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.core.exceptions import validation_error_handler


class _SamplePayload(BaseModel):
    name: str
    daily_rate: int


def _build_app() -> FastAPI:
    app = FastAPI()
    app.add_exception_handler(RequestValidationError, validation_error_handler)

    @app.post("/sample")
    async def sample(payload: _SamplePayload) -> dict:
        return {"ok": True}

    return app


def test_missing_field_returns_korean_detail():
    client = TestClient(_build_app())

    response = client.post("/sample", json={"name": "김철수"})

    assert response.status_code == 422
    body = response.json()
    assert isinstance(body["detail"], str)
    assert "daily_rate" in body["detail"]
    assert "필수 항목입니다" in body["detail"]
    assert "Field required" not in body["detail"]


def test_wrong_type_returns_korean_detail():
    client = TestClient(_build_app())

    response = client.post("/sample", json={"name": "김철수", "daily_rate": "abc"})

    assert response.status_code == 422
    body = response.json()
    assert "숫자" in body["detail"]
