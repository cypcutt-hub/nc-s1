from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.main as main
from app.db.base import Base
from app.models import BaseMode, Defect, Machine, Material, RecommendationRule


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
        machine = Machine(
            name="HSG_3kW_150mm_VSX_NC30E",
            model="Model A",
            laser_power_w=3000,
            lens_focal_length_mm=150,
        )
        steel = Material(name="Steel", material_group="steel", default_gas_branch="N2")
        stainless = Material(
            name="Stainless", material_group="stainless", default_gas_branch="N2"
        )
        carbon = Material(
            name="Carbon", material_group="carbon", default_gas_branch="O2"
        )

        db.add_all(
            [
                machine,
                steel,
                stainless,
                carbon,
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
                Defect(
                    code="warp",
                    name="Warp",
                    gas_branch="N2",
                    is_critical=False,
                ),
                RecommendationRule(
                    defect_code="no_cut",
                    parameter="power",
                    direction="increase",
                    base_delta=0.05,
                    is_active=True,
                ),
                RecommendationRule(
                    defect_code="no_cut",
                    parameter="speed",
                    direction="decrease",
                    base_delta=0.05,
                    is_active=True,
                ),
                RecommendationRule(
                    defect_code="burr",
                    parameter="power",
                    direction="decrease",
                    base_delta=0.05,
                    is_active=True,
                ),
                RecommendationRule(
                    defect_code="burr",
                    parameter="speed",
                    direction="increase",
                    base_delta=0.05,
                    is_active=True,
                ),
                RecommendationRule(
                    defect_code="overburn",
                    parameter="power",
                    direction="decrease",
                    base_delta=0.10,
                    is_active=True,
                ),
            ]
        )
        db.flush()
        db.add_all(
            [
                BaseMode(
                    material_id=stainless.id,
                    machine_id=machine.id,
                    thickness_mm=2.0,
                    gas_type="N2",
                    power_percent=92.0,
                    speed_m_min=3.6,
                    frequency_hz=4500.0,
                    pressure_bar=11.0,
                    focus_mm=-0.3,
                    cutting_height_mm=0.9,
                    duty_cycle_percent=80.0,
                    nozzle_diameter_mm=1.4,
                    trust_level=100,
                ),
                BaseMode(
                    material_id=stainless.id,
                    machine_id=machine.id,
                    thickness_mm=4.0,
                    gas_type="N2",
                    power_percent=88.0,
                    speed_m_min=3.1,
                    frequency_hz=4200.0,
                    pressure_bar=10.0,
                    focus_mm=-0.4,
                    cutting_height_mm=0.95,
                    duty_cycle_percent=75.0,
                    nozzle_diameter_mm=1.5,
                    trust_level=100,
                ),
                BaseMode(
                    material_id=stainless.id,
                    machine_id=machine.id,
                    thickness_mm=6.0,
                    gas_type="N2",
                    power_percent=83.0,
                    speed_m_min=2.6,
                    frequency_hz=3900.0,
                    pressure_bar=9.5,
                    focus_mm=-0.5,
                    cutting_height_mm=1.0,
                    duty_cycle_percent=70.0,
                    nozzle_diameter_mm=1.6,
                    trust_level=100,
                ),
            ]
        )
        db.commit()

    monkeypatch.setattr(main, "SessionLocal", testing_session_local)
    monkeypatch.setattr("app.services.base_mode_selector.SessionLocal", testing_session_local)

    with TestClient(main.app) as test_client:
        yield test_client


def _create_session(client: TestClient, **overrides: float | str) -> dict:
    payload = {
        "machine_name": "HSG_3kW_150mm_VSX_NC30E",
        "material_group": "stainless",
        "thickness_mm": 2.0,
        "gas_branch": "N2",
    }
    payload.update(overrides)
    response = client.post(
        "/sessions",
        json=payload,
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


def _recommend_payload(**overrides: float | int | str | dict[str, float]) -> dict:
    payload = {
        "defect_code": "no_cut",
        "severity_level": 2,
        "current_mode": {
            "power": 980.0,
            "speed": 11.5,
            "frequency": 4800.0,
            "pressure": 7.5,
            "focus": 0.4,
            "height": 1.1,
            "duty_cycle": 62.0,
            "nozzle": 1.6,
        },
    }
    payload.update(overrides)
    return payload


def test_create_session(client: TestClient) -> None:
    response = client.post(
        "/sessions",
        json={
            "machine_name": "HSG_3kW_150mm_VSX_NC30E",
            "material_group": "stainless",
            "thickness_mm": 2.0,
            "gas_branch": "N2",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["id"] > 0
    assert body["machine_name"] == "HSG_3kW_150mm_VSX_NC30E"
    assert body["material_group"] == "stainless"
    assert body["thickness_mm"] == 2.0
    assert body["gas_branch"] == "N2"


def test_list_thicknesses_dictionary(client: TestClient) -> None:
    response = client.get(
        "/dict/thicknesses",
        params={
            "machine_name": "HSG_3kW_150mm_VSX_NC30E",
            "material_group": "stainless",
            "gas_branch": "N2",
        },
    )

    assert response.status_code == 200
    assert response.json() == [
        {"value": 1.0, "label": "1 мм"},
        {"value": 2.0, "label": "2 мм"},
        {"value": 3.0, "label": "3 мм"},
        {"value": 4.0, "label": "4 мм"},
        {"value": 5.0, "label": "5 мм"},
        {"value": 6.0, "label": "6 мм"},
        {"value": 8.0, "label": "8 мм"},
        {"value": 10.0, "label": "10 мм"},
    ]


def test_list_machines_dictionary(client: TestClient) -> None:
    response = client.get("/dictionaries/machines")

    assert response.status_code == 200
    assert response.json() == [
        {
            "value": "HSG_3kW_150mm_VSX_NC30E",
            "label": "HSG 3 кВт, линза 150 мм, голова VSX NC30E",
        }
    ]


def test_list_materials_dictionary(client: TestClient) -> None:
    response = client.get("/dictionaries/materials")

    assert response.status_code == 200
    assert response.json() == [
        {"value": "carbon", "label": "Углеродистая сталь"},
        {"value": "stainless", "label": "Нержавеющая сталь"},
        {"value": "aluminum", "label": "Алюминий"},
    ]


def test_list_gases_dictionary(client: TestClient) -> None:
    response = client.get("/dictionaries/gases")

    assert response.status_code == 200
    assert response.json() == [
        {"value": "O2", "label": "Кислород O2"},
        {"value": "N2", "label": "Азот N2"},
        {"value": "air", "label": "Воздух"},
    ]


def test_list_defects_dictionary(client: TestClient) -> None:
    response = client.get("/dictionaries/defects")

    assert response.status_code == 200
    assert response.json() == [
        {"value": "burr", "label": "Грат снизу"},
        {"value": "no_cut", "label": "Непрорез"},
        {"value": "overburn", "label": "Пережог / оплавление"},
    ]


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

    assert (
        client.post(f"/sessions/{session['id']}/iterations", json=first).status_code
        == 201
    )
    assert (
        client.post(f"/sessions/{session['id']}/iterations", json=second).status_code
        == 201
    )

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


def test_get_base_mode_exact_match(client: TestClient) -> None:
    session = _create_session(
        client, material_group="stainless", gas_branch="N2", thickness_mm=2.0
    )

    response = client.get(f"/sessions/{session['id']}/base-mode")

    assert response.status_code == 200
    body = response.json()
    assert body["power"] == 92.0
    assert body["speed"] == 3.6
    assert body["frequency"] == 4500.0
    assert body["pressure"] == 11.0
    assert body["focus"] == -0.3
    assert body["height"] == 0.9
    assert body["duty_cycle"] == 80.0
    assert body["nozzle"] == 1.4
    assert body["explanation"] == "Использовано точное совпадение"


def test_get_base_mode_falls_back_to_nearest_thickness(client: TestClient) -> None:
    session = _create_session(
        client, material_group="stainless", gas_branch="N2", thickness_mm=5.0
    )

    response = client.get(f"/sessions/{session['id']}/base-mode")

    assert response.status_code == 200
    body = response.json()
    assert body["power"] == 88.0
    assert body["speed"] == 3.1
    assert body["nozzle"] == 1.5
    assert body["explanation"] == "Использована ближайшая толщина 4 мм вместо 5 мм"


def test_get_base_mode_no_match_returns_404(client: TestClient) -> None:
    session = _create_session(
        client, material_group="aluminum", gas_branch="air", thickness_mm=1.0
    )

    response = client.get(f"/sessions/{session['id']}/base-mode")

    assert response.status_code == 404
    assert "base mode not found" in response.json()["detail"]


def test_recommend_base_mode_returns_exact_match(client: TestClient) -> None:
    response = client.get(
        "/base-mode/recommend",
        params={
            "machine_name": "HSG_3kW_150mm_VSX_NC30E",
            "material_group": "stainless",
            "gas_branch": "N2",
            "thickness_mm": 4.0,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["power"] == 88.0
    assert body["speed"] == 3.1
    assert body["frequency"] == 4200.0
    assert body["pressure"] == 10.0
    assert body["focus"] == -0.4
    assert body["height"] == 0.95
    assert body["duty_cycle"] == 75.0
    assert body["nozzle"] == 1.5


def test_recommend_base_mode_interpolates_values(client: TestClient) -> None:
    response = client.get(
        "/base-mode/recommend",
        params={
            "machine_name": "HSG_3kW_150mm_VSX_NC30E",
            "material_group": "stainless",
            "gas_branch": "N2",
            "thickness_mm": 5.0,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["speed"] == pytest.approx(2.85)
    assert body["pressure"] == pytest.approx(9.75)
    assert body["focus"] == pytest.approx(-0.45)
    assert body["height"] == pytest.approx(0.975)


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
            "machine_name": "HSG_3kW_150mm_VSX_NC30E",
            "material_group": "stainless",
            "thickness_mm": 0,
            "gas_branch": "N2",
        },
    )

    assert response.status_code == 422


def test_unlisted_thickness_rejected(client: TestClient) -> None:
    response = client.post(
        "/sessions",
        json={
            "machine_name": "HSG_3kW_150mm_VSX_NC30E",
            "material_group": "stainless",
            "thickness_mm": 2.5,
            "gas_branch": "N2",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "thickness is not allowed"


def test_session_creation_rejected_when_thickness_list_empty(client: TestClient) -> None:
    response = client.post(
        "/sessions",
        json={
            "machine_name": "UNKNOWN_MACHINE",
            "material_group": "stainless",
            "thickness_mm": 2.0,
            "gas_branch": "N2",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "no allowed thicknesses for selected machine/material/gas"


def test_rules_list_returns_seeded_rules(client: TestClient) -> None:
    response = client.get("/rules")

    assert response.status_code == 200
    body = response.json()
    assert len(body) >= 5
    assert all("defect_code" in rule for rule in body)
    assert all("parameter" in rule for rule in body)
    assert all("direction" in rule for rule in body)


def test_create_rule(client: TestClient) -> None:
    response = client.post(
        "/rules",
        json={
            "defect_code": "warp",
            "parameter": "pressure",
            "direction": "increase",
            "base_delta": 0.2,
            "is_active": True,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["id"] > 0
    assert body["defect_code"] == "warp"
    assert body["parameter"] == "pressure"
    assert body["direction"] == "increase"
    assert body["base_delta"] == 0.2
    assert body["is_active"] is True


def test_update_rule(client: TestClient) -> None:
    created = client.post(
        "/rules",
        json={
            "defect_code": "warp",
            "parameter": "frequency",
            "direction": "increase",
            "base_delta": 0.08,
        },
    )
    assert created.status_code == 201
    rule_id = created.json()["id"]

    response = client.patch(
        f"/rules/{rule_id}",
        json={
            "parameter": "pressure",
            "direction": "decrease",
            "base_delta": 0.12,
            "is_active": False,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == rule_id
    assert body["parameter"] == "pressure"
    assert body["direction"] == "decrease"
    assert body["base_delta"] == 0.12
    assert body["is_active"] is False


def test_invalid_parameter_rejected(client: TestClient) -> None:
    response = client.post(
        "/rules",
        json={
            "defect_code": "warp",
            "parameter": "temperature",
            "direction": "increase",
            "base_delta": 0.1,
        },
    )

    assert response.status_code == 422


def test_recommendation_for_no_cut(client: TestClient) -> None:
    session = _create_session(client)
    assert (
        client.post(
            f"/sessions/{session['id']}/iterations", json=_iteration_payload()
        ).status_code
        == 201
    )

    response = client.post(f"/sessions/{session['id']}/recommend")

    assert response.status_code == 200
    body = response.json()
    assert body["power_after"] == pytest.approx(1038.8)
    assert body["speed_after"] == pytest.approx(10.465)
    assert body["frequency_after"] == 4800.0
    assert body["focus_after"] == 0.4
    assert body["pressure_after"] == 7.5
    assert body["height_after"] == 1.1
    assert body["duty_cycle_after"] == 62.0
    assert body["nozzle_after"] == 1.6
    assert any("rule from DB" in line for line in body["explanation"])
    assert "Severity level 2 applied multiplier x1.5" in body["explanation"]


def test_recommendation_on_empty_session_with_body(client: TestClient) -> None:
    session = _create_session(client)

    response = client.post(
        f"/sessions/{session['id']}/recommend",
        json=_recommend_payload(),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["power_after"] == pytest.approx(1038.8)
    assert body["speed_after"] == pytest.approx(10.465)
    assert body["frequency_after"] == 4800.0
    assert body["pressure_after"] == 7.5
    assert body["focus_after"] == 0.4
    assert body["height_after"] == 1.1
    assert body["duty_cycle_after"] == 62.0
    assert body["nozzle_after"] == 1.6
    assert any("rule from DB" in line for line in body["explanation"])


def test_recommendation_uses_provided_defect_and_severity(client: TestClient) -> None:
    session = _create_session(client)
    assert (
        client.post(
            f"/sessions/{session['id']}/iterations",
            json=_iteration_payload(
                defect_code="burr",
                severity_level=1,
                power_after=1000.0,
                speed_after=12.0,
            ),
        ).status_code
        == 201
    )

    response = client.post(
        f"/sessions/{session['id']}/recommend",
        json=_recommend_payload(
            defect_code="overburn",
            severity_level=3,
            current_mode={
                "power": 1000.0,
                "speed": 12.0,
                "frequency": 4800.0,
                "pressure": 7.5,
                "focus": 0.4,
                "height": 1.1,
                "duty_cycle": 62.0,
                "nozzle": 1.6,
            },
        ),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["power_after"] == pytest.approx(840.0)
    assert body["speed_after"] == 12.0
    assert "Applied power decrease (0.1) - rule from DB" in body["explanation"]
    assert "Severity level 3 applied multiplier x2" in body["explanation"]


def test_recommendation_without_body_requires_latest_iteration(
    client: TestClient,
) -> None:
    session = _create_session(client)

    response = client.post(f"/sessions/{session['id']}/recommend")

    assert response.status_code == 400
    assert response.json()["detail"] == "session has no iterations"


def test_recommendation_for_burr(client: TestClient) -> None:
    session = _create_session(client)
    payload = _iteration_payload(
        defect_code="burr", severity_level=1, power_after=1000.0, speed_after=12.0
    )
    assert (
        client.post(f"/sessions/{session['id']}/iterations", json=payload).status_code
        == 201
    )

    response = client.post(f"/sessions/{session['id']}/recommend")

    assert response.status_code == 200
    body = response.json()
    assert body["power_after"] == pytest.approx(960.0)
    assert body["speed_after"] == pytest.approx(12.72)
    assert body["frequency_after"] == payload["frequency_after"]
    assert body["height_after"] == payload["height_after"]
    assert body["duty_cycle_after"] == payload["duty_cycle_after"]
    assert body["nozzle_after"] == payload["nozzle_after"]


def test_recommendation_respects_severity(client: TestClient) -> None:
    session = _create_session(client)
    first = _iteration_payload(
        step_number=1, defect_code="overburn", severity_level=1, power_after=1000.0
    )
    second = _iteration_payload(
        step_number=2, defect_code="overburn", severity_level=3, power_after=1000.0
    )
    assert (
        client.post(f"/sessions/{session['id']}/iterations", json=first).status_code
        == 201
    )
    assert (
        client.post(f"/sessions/{session['id']}/iterations", json=second).status_code
        == 201
    )

    response = client.post(f"/sessions/{session['id']}/recommend")

    assert response.status_code == 200
    body = response.json()
    assert body["power_after"] == pytest.approx(840.0)
    assert body["frequency_after"] == second["frequency_after"]


def test_recommendation_differs_with_thickness_context(client: TestClient) -> None:
    thin_session = _create_session(client, thickness_mm=1.0)
    thick_session = _create_session(client, thickness_mm=10.0)

    payload = _iteration_payload(
        defect_code="no_cut", severity_level=2, power_after=1000.0, speed_after=12.0
    )
    assert (
        client.post(
            f"/sessions/{thin_session['id']}/iterations", json=payload
        ).status_code
        == 201
    )
    assert (
        client.post(
            f"/sessions/{thick_session['id']}/iterations", json=payload
        ).status_code
        == 201
    )

    thin_recommend = client.post(f"/sessions/{thin_session['id']}/recommend")
    thick_recommend = client.post(f"/sessions/{thick_session['id']}/recommend")

    assert thin_recommend.status_code == 200
    assert thick_recommend.status_code == 200
    assert thin_recommend.json()["power_after"] != thick_recommend.json()["power_after"]
    assert thin_recommend.json()["speed_after"] != thick_recommend.json()["speed_after"]
    assert any(
        "Thickness 1.0 mm reduced power impact" == line
        for line in thin_recommend.json()["explanation"]
    )
    assert any(
        "Thickness 10.0 mm increased power impact and reduced speed impact" == line
        for line in thick_recommend.json()["explanation"]
    )


def test_recommendation_differs_with_gas_branch_context(client: TestClient) -> None:
    o2_session = _create_session(
        client,
        material_group="carbon",
        gas_branch="O2",
        thickness_mm=4.0,
    )
    n2_session = _create_session(
        client,
        material_group="stainless",
        gas_branch="N2",
        thickness_mm=4.0,
    )

    payload = _iteration_payload(
        defect_code="no_cut", severity_level=2, power_after=1000.0, speed_after=12.0
    )
    assert (
        client.post(
            f"/sessions/{o2_session['id']}/iterations", json=payload
        ).status_code
        == 201
    )
    assert (
        client.post(
            f"/sessions/{n2_session['id']}/iterations", json=payload
        ).status_code
        == 201
    )

    o2_recommend = client.post(f"/sessions/{o2_session['id']}/recommend")
    n2_recommend = client.post(f"/sessions/{n2_session['id']}/recommend")

    assert o2_recommend.status_code == 200
    assert n2_recommend.status_code == 200
    assert o2_recommend.json()["power_after"] != n2_recommend.json()["power_after"]
    assert o2_recommend.json()["speed_after"] != n2_recommend.json()["speed_after"]
    assert "Gas O2 amplified power changes" in o2_recommend.json()["explanation"]
    assert "Gas N2 increased speed sensitivity" in n2_recommend.json()["explanation"]


def test_recommendation_differs_with_material_group_context(client: TestClient) -> None:
    stainless_session = _create_session(
        client, material_group="stainless", gas_branch="N2", thickness_mm=4.0
    )
    carbon_session = _create_session(
        client, material_group="carbon", gas_branch="O2", thickness_mm=4.0
    )

    payload = _iteration_payload(
        defect_code="overburn", severity_level=2, power_after=1000.0
    )
    assert (
        client.post(
            f"/sessions/{stainless_session['id']}/iterations", json=payload
        ).status_code
        == 201
    )
    assert (
        client.post(
            f"/sessions/{carbon_session['id']}/iterations", json=payload
        ).status_code
        == 201
    )

    stainless_recommend = client.post(f"/sessions/{stainless_session['id']}/recommend")
    carbon_recommend = client.post(f"/sessions/{carbon_session['id']}/recommend")

    assert stainless_recommend.status_code == 200
    assert carbon_recommend.status_code == 200
    assert (
        stainless_recommend.json()["power_after"]
        != carbon_recommend.json()["power_after"]
    )
    assert (
        "Material stainless reduced power sensitivity"
        in stainless_recommend.json()["explanation"]
    )
    assert (
        "Material carbon increased power sensitivity"
        in carbon_recommend.json()["explanation"]
    )


def test_recommendation_explanation_changes_with_severity(client: TestClient) -> None:
    low_session = _create_session(client)
    high_session = _create_session(client)

    low_payload = _iteration_payload(
        defect_code="no_cut", severity_level=1, power_after=1000.0, speed_after=12.0
    )
    high_payload = _iteration_payload(
        defect_code="no_cut", severity_level=3, power_after=1000.0, speed_after=12.0
    )
    assert (
        client.post(
            f"/sessions/{low_session['id']}/iterations", json=low_payload
        ).status_code
        == 201
    )
    assert (
        client.post(
            f"/sessions/{high_session['id']}/iterations", json=high_payload
        ).status_code
        == 201
    )

    low_recommend = client.post(f"/sessions/{low_session['id']}/recommend")
    high_recommend = client.post(f"/sessions/{high_session['id']}/recommend")

    assert low_recommend.status_code == 200
    assert high_recommend.status_code == 200
    assert (
        "Severity level 1 applied multiplier x1" in low_recommend.json()["explanation"]
    )
    assert (
        "Severity level 3 applied multiplier x2" in high_recommend.json()["explanation"]
    )


def test_recommendation_empty_session_returns_error(client: TestClient) -> None:
    session = _create_session(client)

    response = client.post(f"/sessions/{session['id']}/recommend")

    assert response.status_code == 400


def test_recommendation_disabling_rule_changes_result(client: TestClient) -> None:
    session = _create_session(client)
    payload = _iteration_payload(
        defect_code="no_cut", severity_level=2, power_after=1000.0, speed_after=12.0
    )
    assert (
        client.post(f"/sessions/{session['id']}/iterations", json=payload).status_code
        == 201
    )

    before = client.post(f"/sessions/{session['id']}/recommend")
    assert before.status_code == 200

    with main.SessionLocal() as db:
        speed_rule = (
            db.query(RecommendationRule)
            .filter(
                RecommendationRule.defect_code == "no_cut",
                RecommendationRule.parameter == "speed",
            )
            .first()
        )
        assert speed_rule is not None
        speed_rule.is_active = False
        db.commit()

    after = client.post(f"/sessions/{session['id']}/recommend")
    assert after.status_code == 200
    assert before.json()["speed_after"] != after.json()["speed_after"]
    assert after.json()["speed_after"] == payload["speed_after"]


def test_recommendation_changes_after_rule_update_via_api(client: TestClient) -> None:
    session = _create_session(client)
    payload = _iteration_payload(
        defect_code="no_cut", severity_level=2, power_after=1000.0, speed_after=12.0
    )
    assert (
        client.post(f"/sessions/{session['id']}/iterations", json=payload).status_code
        == 201
    )

    before = client.post(f"/sessions/{session['id']}/recommend")
    assert before.status_code == 200

    rules = client.get("/rules")
    assert rules.status_code == 200
    power_rule = next(
        rule
        for rule in rules.json()
        if rule["defect_code"] == "no_cut" and rule["parameter"] == "power"
    )

    patch_response = client.patch(
        f"/rules/{power_rule['id']}",
        json={"base_delta": 0.2},
    )
    assert patch_response.status_code == 200

    after = client.post(f"/sessions/{session['id']}/recommend")
    assert after.status_code == 200
    assert before.json()["power_after"] != after.json()["power_after"]


def test_disable_rule_via_api(client: TestClient) -> None:
    rules = client.get("/rules")
    assert rules.status_code == 200
    speed_rule = next(
        rule
        for rule in rules.json()
        if rule["defect_code"] == "no_cut" and rule["parameter"] == "speed"
    )

    response = client.patch(f"/rules/{speed_rule['id']}", json={"is_active": False})

    assert response.status_code == 200
    assert response.json()["is_active"] is False


def test_recommendation_with_defect_without_rules_returns_unchanged_mode(
    client: TestClient,
) -> None:
    session = _create_session(client)

    response = client.post(
        f"/sessions/{session['id']}/recommend",
        json=_recommend_payload(defect_code="warp"),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["power_after"] == 980.0
    assert body["speed_after"] == 11.5
    assert body["frequency_after"] == 4800.0
    assert (
        "No active rules for defect warp; rule from DB not found" in body["explanation"]
    )


def test_recommendation_explanation_includes_db_reference(client: TestClient) -> None:
    session = _create_session(client)
    assert (
        client.post(
            f"/sessions/{session['id']}/iterations", json=_iteration_payload()
        ).status_code
        == 201
    )

    response = client.post(f"/sessions/{session['id']}/recommend")

    assert response.status_code == 200
    explanation = response.json()["explanation"]
    assert any("rule from DB" in line for line in explanation)
    assert any("Applied power increase" in line for line in explanation)
