from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

import app.main as main
from app.db.base import Base
from app.models import Defect


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(bind=engine)

    with TestingSessionLocal() as db:
        db.add(
            Defect(
                code="no_cut",
                name="No Cut",
                gas_branch="N2",
                is_critical=True,
            )
        )
        db.commit()

    monkeypatch.setattr(main, "SessionLocal", TestingSessionLocal)

    with TestClient(main.app) as test_client:
        yield test_client


def _create_session(client: TestClient) -> dict:
    response = client.post(
        "/sessions",
        json={
            "machine_name": "Machine A",
            "material_group": "steel",
            "thickness_mm": 2.5,
            "gas_branch": "N2",
        },
    )

    assert response.status_code == 201
    return response.json()


def test_create_session(client: TestClient) -> None:
    response = client.post(
        "/sessions",
        json={
            "machine_name": "Machine A",
            "material_group": "steel",
            "thickness_mm": 2.5,
            "gas_branch": "N2",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["id"] > 0
    assert body["machine_name"] == "Machine A"
    assert body["material_group"] == "steel"
    assert body["thickness_mm"] == 2.5
    assert body["gas_branch"] == "N2"


def test_read_session_with_empty_iterations(client: TestClient) -> None:
    session = _create_session(client)

    response = client.get(f"/sessions/{session['id']}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == session["id"]
    assert body["iterations"] == []


def test_add_iteration(client: TestClient) -> None:
    session = _create_session(client)

    response = client.post(
        f"/sessions/{session['id']}/iterations",
        json={
            "step_number": 1,
            "defect_code": "no_cut",
            "severity_level": 2,
            "power_before": 1000.0,
            "speed_before": 12.0,
            "focus_before": 0.5,
            "pressure_before": 8.0,
            "power_after": 980.0,
            "speed_after": 11.5,
            "focus_after": 0.4,
            "pressure_after": 7.5,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["id"] > 0
    assert body["session_id"] == session["id"]
    assert body["defect_code"] == "no_cut"
    assert body["severity_level"] == 2


def test_read_session_with_iterations(client: TestClient) -> None:
    session = _create_session(client)

    first = {
        "step_number": 2,
        "defect_code": "no_cut",
        "severity_level": 1,
        "power_before": 1000.0,
        "speed_before": 12.0,
        "focus_before": 0.5,
        "pressure_before": 8.0,
        "power_after": 990.0,
        "speed_after": 11.8,
        "focus_after": 0.4,
        "pressure_after": 7.8,
    }
    second = {
        "step_number": 1,
        "defect_code": "no_cut",
        "severity_level": 2,
        "power_before": 990.0,
        "speed_before": 11.8,
        "focus_before": 0.4,
        "pressure_before": 7.8,
        "power_after": 970.0,
        "speed_after": 11.5,
        "focus_after": 0.3,
        "pressure_after": 7.5,
    }

    assert client.post(f"/sessions/{session['id']}/iterations", json=first).status_code == 201
    assert client.post(f"/sessions/{session['id']}/iterations", json=second).status_code == 201

    response = client.get(f"/sessions/{session['id']}")

    assert response.status_code == 200
    body = response.json()
    assert [iteration["step_number"] for iteration in body["iterations"]] == [1, 2]


def test_unknown_session_id_returns_404(client: TestClient) -> None:
    get_response = client.get("/sessions/999")
    post_response = client.post(
        "/sessions/999/iterations",
        json={
            "step_number": 1,
            "defect_code": "no_cut",
            "severity_level": 2,
            "power_before": 1000.0,
            "speed_before": 12.0,
            "focus_before": 0.5,
            "pressure_before": 8.0,
            "power_after": 980.0,
            "speed_after": 11.5,
            "focus_after": 0.4,
            "pressure_after": 7.5,
        },
    )

    assert get_response.status_code == 404
    assert post_response.status_code == 404


def test_unknown_defect_code_returns_client_error(client: TestClient) -> None:
    session = _create_session(client)

    response = client.post(
        f"/sessions/{session['id']}/iterations",
        json={
            "step_number": 1,
            "defect_code": "unknown_defect",
            "severity_level": 2,
            "power_before": 1000.0,
            "speed_before": 12.0,
            "focus_before": 0.5,
            "pressure_before": 8.0,
            "power_after": 980.0,
            "speed_after": 11.5,
            "focus_after": 0.4,
            "pressure_after": 7.5,
        },
    )

    assert response.status_code == 400

    session_response = client.get(f"/sessions/{session['id']}")
    assert session_response.status_code == 200
    assert session_response.json()["iterations"] == []


def test_invalid_severity_level_rejected(client: TestClient) -> None:
    session = _create_session(client)

    response = client.post(
        f"/sessions/{session['id']}/iterations",
        json={
            "step_number": 1,
            "defect_code": "no_cut",
            "severity_level": 4,
            "power_before": 1000.0,
            "speed_before": 12.0,
            "focus_before": 0.5,
            "pressure_before": 8.0,
            "power_after": 980.0,
            "speed_after": 11.5,
            "focus_after": 0.4,
            "pressure_after": 7.5,
        },
    )

    assert response.status_code == 422


def test_invalid_thickness_rejected(client: TestClient) -> None:
    response = client.post(
        "/sessions",
        json={
            "machine_name": "Machine A",
            "material_group": "steel",
            "thickness_mm": 0,
            "gas_branch": "N2",
        },
    )

    assert response.status_code == 422
