from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

import app.main as main


client = TestClient(main.app)


class _OkSession:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return None

    def execute(self, *_args, **_kwargs):
        return 1


class _FailedSession(_OkSession):
    def execute(self, *_args, **_kwargs):
        raise SQLAlchemyError("db down")


def test_health_check() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_db_health_check_ok(monkeypatch) -> None:
    monkeypatch.setattr(main, "SessionLocal", _OkSession)

    response = client.get("/db-health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_db_health_check_unavailable(monkeypatch) -> None:
    monkeypatch.setattr(main, "SessionLocal", _FailedSession)

    response = client.get("/db-health")

    assert response.status_code == 503
    assert response.json() == {"detail": "database unavailable"}

