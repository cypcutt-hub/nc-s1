from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

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
    testing_session_local = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(bind=engine)

    with testing_session_local() as db:
        db.add_all(
            [
                Defect(
                code="no_cut",
                name="No Cut",
                gas_branch="N2",
                is_critical=True,
                ),
                Defect(
                    code="burr",
                    name="Burr",
                    gas_branch="N2",
                    is_critical=False,
                ),
                Defect(
                    code="overburn",
                    name="Overburn",
                    gas_branch="N2",
                    is_critical=True,
                ),
            ]
        )
        db.commit()

    monkeypatch.setattr(main, "SessionLocal", testing_session_local)

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


def _iteration_payload(**overrides: float | int | str) -> dict:
    payload = {
        "step_number": 1,
        "defect_code": "no_cut",
        "severity_level": 2,
        "power_before": 1000.0,
        "speed_before": 12.0,
        "frequency_before": 5000.0,
        "pressure_before": 8.0,
        "focus_before": 0.5,
        "height_before": 1.2,
        "duty_cycle_before": 65.0,
        "nozzle_before": 1.6,
        "power_after": 980.0,
        "speed_after": 11.5,
        "frequency_after": 4800.0,
        "pressure_after": 7.5,
        "focus_after": 0.4,
        "height_after": 1.1,
        "duty_cycle_after": 62.0,
        "nozzle_after": 1.6,
    }
    payload.update(overrides)
    return payload


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
        json=_iteration_payload(),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["id"] > 0
    assert body["session_id"] == session["id"]
    assert body["defect_code"] == "no_cut"
    assert body["severity_level"] == 2
    assert body["frequency_before"] == 5000.0
    assert body["height_after"] == 1.1
    assert body["duty_cycle_after"] == 62.0
    assert body["nozzle_after"] == 1.6


def test_read_session_with_iterations(client: TestClient) -> None:
    session = _create_session(client)

    first = _iteration_payload(step_number=2, severity_level=1)
    second = _iteration_payload(
        step_number=1,
        severity_level=2,
        power_before=990.0,
        speed_before=11.8,
        frequency_before=4900.0,
        pressure_before=7.8,
        focus_before=0.4,
        height_before=1.1,
        duty_cycle_before=63.0,
        power_after=970.0,
        speed_after=11.5,
        frequency_after=4700.0,
        pressure_after=7.5,
        focus_after=0.3,
        height_after=1.0,
        duty_cycle_after=60.0,
    )

    assert client.post(f"/sessions/{session['id']}/iterations", json=first).status_code == 201
    assert client.post(f"/sessions/{session['id']}/iterations", json=second).status_code == 201

    response = client.get(f"/sessions/{session['id']}")

    assert response.status_code == 200
    body = response.json()
    assert [iteration["step_number"] for iteration in body["iterations"]] == [1, 2]
    assert body["iterations"][0]["frequency_after"] == 4700.0


def test_unknown_session_id_returns_404(client: TestClient) -> None:
    get_response = client.get("/sessions/999")
    post_response = client.post(
        "/sessions/999/iterations",
        json=_iteration_payload(),
    )

    assert get_response.status_code == 404
    assert post_response.status_code == 404


def test_unknown_defect_code_returns_client_error(client: TestClient) -> None:
    session = _create_session(client)

    response = client.post(
        f"/sessions/{session['id']}/iterations",
        json=_iteration_payload(defect_code="unknown_defect"),
    )

    assert response.status_code == 400

    session_response = client.get(f"/sessions/{session['id']}")
    assert session_response.status_code == 200
    assert session_response.json()["iterations"] == []


def test_invalid_severity_level_rejected(client: TestClient) -> None:
    session = _create_session(client)

    response = client.post(
        f"/sessions/{session['id']}/iterations",
        json=_iteration_payload(severity_level=4),
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


def test_recommendation_for_no_cut(client: TestClient) -> None:
    session = _create_session(client)
    assert client.post(f"/sessions/{session['id']}/iterations", json=_iteration_payload()).status_code == 201

    response = client.post(f"/sessions/{session['id']}/recommend")

    assert response.status_code == 200
    body = response.json()
    assert body["power_after"] == pytest.approx(1053.5)
    assert body["speed_after"] == pytest.approx(10.6375)
    assert body["frequency_after"] == 4800.0
    assert body["focus_after"] == 0.4
    assert body["pressure_after"] == 7.5
    assert body["height_after"] == 1.1
    assert body["duty_cycle_after"] == 62.0
    assert body["nozzle_after"] == 1.6


def test_recommendation_for_burr(client: TestClient) -> None:
    session = _create_session(client)
    payload = _iteration_payload(defect_code="burr", severity_level=1, power_after=1000.0, speed_after=12.0)
    assert client.post(f"/sessions/{session['id']}/iterations", json=payload).status_code == 201

    response = client.post(f"/sessions/{session['id']}/recommend")

    assert response.status_code == 200
    body = response.json()
    assert body["power_after"] == pytest.approx(950.0)
    assert body["speed_after"] == pytest.approx(12.6)
    assert body["frequency_after"] == payload["frequency_after"]
    assert body["height_after"] == payload["height_after"]
    assert body["duty_cycle_after"] == payload["duty_cycle_after"]
    assert body["nozzle_after"] == payload["nozzle_after"]


def test_recommendation_respects_severity(client: TestClient) -> None:
    session = _create_session(client)
    first = _iteration_payload(step_number=1, defect_code="overburn", severity_level=1, power_after=1000.0)
    second = _iteration_payload(step_number=2, defect_code="overburn", severity_level=3, power_after=1000.0)
    assert client.post(f"/sessions/{session['id']}/iterations", json=first).status_code == 201
    assert client.post(f"/sessions/{session['id']}/iterations", json=second).status_code == 201

    response = client.post(f"/sessions/{session['id']}/recommend")

    assert response.status_code == 200
    body = response.json()
    assert body["power_after"] == pytest.approx(800.0)
    assert body["frequency_after"] == second["frequency_after"]


def test_recommendation_empty_session_returns_error(client: TestClient) -> None:
    session = _create_session(client)

    response = client.post(f"/sessions/{session['id']}/recommend")

    assert response.status_code == 400
