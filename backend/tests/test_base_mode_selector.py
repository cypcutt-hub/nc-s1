from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models import BaseMode, Machine, Material
from app.services.base_mode_selector import get_best_base_mode


@pytest.fixture()
def selector_db(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session_local = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(bind=engine)

    with testing_session_local() as db:
        machine = Machine(
            name="Machine A",
            model="Model A",
            laser_power_w=3000,
            lens_focal_length_mm=150,
        )
        material = Material(
            name="Steel",
            material_group="steel",
            default_gas_branch="N2",
        )
        db.add_all([machine, material])
        db.flush()

        db.add_all(
            [
                BaseMode(
                    machine_id=machine.id,
                    material_id=material.id,
                    thickness_mm=2.0,
                    gas_type="N2",
                    power_percent=90.0,
                    speed_m_min=4.0,
                    frequency_hz=4000.0,
                    pressure_bar=10.0,
                    focus_mm=-0.2,
                    cutting_height_mm=0.8,
                    duty_cycle_percent=80.0,
                    nozzle_diameter_mm=1.2,
                    trust_level=60,
                ),
                BaseMode(
                    machine_id=machine.id,
                    material_id=material.id,
                    thickness_mm=2.0,
                    gas_type="N2",
                    power_percent=91.0,
                    speed_m_min=4.1,
                    frequency_hz=4010.0,
                    pressure_bar=10.1,
                    focus_mm=-0.1,
                    cutting_height_mm=0.82,
                    duty_cycle_percent=81.0,
                    nozzle_diameter_mm=1.3,
                    trust_level=90,
                ),
                BaseMode(
                    machine_id=machine.id,
                    material_id=material.id,
                    thickness_mm=4.0,
                    gas_type="N2",
                    power_percent=85.0,
                    speed_m_min=3.0,
                    frequency_hz=3800.0,
                    pressure_bar=9.0,
                    focus_mm=-0.4,
                    cutting_height_mm=1.0,
                    duty_cycle_percent=75.0,
                    nozzle_diameter_mm=1.5,
                    trust_level=80,
                ),
            ]
        )
        db.commit()

    monkeypatch.setattr("app.services.base_mode_selector.SessionLocal", testing_session_local)
    yield


def test_get_best_base_mode_exact_match(selector_db) -> None:
    mode = get_best_base_mode("Machine A", "steel", "N2", 4.0)

    assert mode is not None
    assert mode.thickness_mm == 4.0
    assert mode.speed_m_min == 3.0


def test_get_best_base_mode_uses_interpolation(selector_db) -> None:
    mode = get_best_base_mode("Machine A", "steel", "N2", 3.0)

    assert mode is not None
    assert mode.thickness_mm == 3.0
    assert mode.speed_m_min == pytest.approx(3.55)
    assert mode.pressure_bar == pytest.approx(9.55)
    assert mode.focus_mm == pytest.approx(-0.25)
    assert mode.cutting_height_mm == pytest.approx(0.91)


def test_get_best_base_mode_picks_highest_trust_on_same_thickness(selector_db) -> None:
    mode = get_best_base_mode("Machine A", "steel", "N2", 2.0)

    assert mode is not None
    assert mode.trust_level == 90
    assert mode.power_percent == 91.0


def test_get_best_base_mode_returns_none_when_missing(selector_db) -> None:
    mode = get_best_base_mode("Unknown Machine", "steel", "N2", 3.0)

    assert mode is None
