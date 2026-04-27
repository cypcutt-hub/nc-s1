from pathlib import Path

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.db.import_base_modes import (
    BaseModesImportError,
    DEFAULT_MACHINE_LASER_POWER_W,
    DEFAULT_MACHINE_LENS_FOCAL_LENGTH_MM,
    DEFAULT_MACHINE_MODEL,
    DEFAULT_TRUST_LEVEL,
    load_csv_rows,
    parse_csv_row,
    upsert_base_modes,
)
from app.models import BaseMode, Machine, Material


def _write_csv(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


@pytest.fixture()
def sqlite_session_local(monkeypatch: pytest.MonkeyPatch):
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    testing_session_local = sessionmaker(bind=engine, autocommit=False, autoflush=False, class_=Session)

    monkeypatch.setattr("app.db.import_base_modes.SessionLocal", testing_session_local)

    yield testing_session_local

    Base.metadata.drop_all(engine)
    engine.dispose()


def test_parse_csv_row_accepts_valid_data() -> None:
    row = {
        "machine_name": "LaserCell-3015",
        "material_group": "carbon",
        "gas_branch": "O2",
        "thickness_mm": "3",
        "power": "85",
        "speed": "2.4",
        "frequency": "0",
        "pressure": "0.8",
        "focus": "-0.5",
        "height": "0.8",
        "duty_cycle": "100",
        "nozzle": "1.2",
    }

    parsed = parse_csv_row(row, 2)

    assert parsed.machine_name == "LaserCell-3015"
    assert parsed.material_group == "carbon"
    assert parsed.gas_branch == "O2"
    assert parsed.thickness_mm == 3.0
    assert parsed.nozzle_diameter_mm == 1.2
    assert parsed.trust_level == DEFAULT_TRUST_LEVEL


def test_parse_csv_row_maps_legacy_material_group_aliases() -> None:
    parsed = parse_csv_row(
        {
            "machine_name": "LaserCell-3015",
            "material_group": "stainless_steel",
            "gas_branch": "N2",
            "thickness_mm": "3",
            "power": "85",
            "speed": "2.4",
            "frequency": "0",
            "pressure": "0.8",
            "focus": "-0.5",
            "height": "0.8",
            "duty_cycle": "100",
            "nozzle": "1.2",
        },
        2,
    )

    assert parsed.material_group == "stainless"


def test_load_csv_rows_fails_when_required_columns_are_missing(tmp_path: Path) -> None:
    csv_path = _write_csv(
        tmp_path / "base_modes.csv",
        "machine_name,material_group\nLaserCell-3015,carbon_steel\n",
    )

    with pytest.raises(BaseModesImportError, match="missing required columns"):
        load_csv_rows(csv_path)


def test_load_csv_rows_fails_for_invalid_numeric_field(tmp_path: Path) -> None:
    csv_path = _write_csv(
        tmp_path / "base_modes.csv",
        (
            "machine_name,material_group,gas_branch,thickness_mm,power,speed,frequency,"
            "pressure,focus,height,duty_cycle,nozzle\n"
            "LaserCell-3015,carbon,O2,not_a_number,85,2.4,0,0.8,-0.5,0.8,100,1.2\n"
        ),
    )

    with pytest.raises(BaseModesImportError, match="thickness_mm"):
        load_csv_rows(csv_path)


def test_load_csv_rows_supports_comma_delimiter(tmp_path: Path) -> None:
    csv_path = _write_csv(
        tmp_path / "base_modes.csv",
        (
            "machine_name,material_group,gas_branch,thickness_mm,power,speed,frequency,"
            "pressure,focus,height,duty_cycle,nozzle\n"
            "LaserCell-3015,carbon,O2,3.0,85,2.4,0,0.8,-0.5,0.8,100,1.2\n"
        ),
    )

    rows = load_csv_rows(csv_path)

    assert len(rows) == 1
    assert rows[0].material_group == "carbon"


def test_load_csv_rows_supports_semicolon_delimiter(tmp_path: Path) -> None:
    csv_path = _write_csv(
        tmp_path / "base_modes.csv",
        (
            "machine_name;material_group;gas_branch;thickness_mm;power;speed;frequency;"
            "pressure;focus;height;duty_cycle;nozzle\n"
            "LaserCell-3015;stainless;N2;3.0;85;2.4;0;0.8;-0.5;0.8;100;1.2\n"
        ),
    )

    rows = load_csv_rows(csv_path)

    assert len(rows) == 1
    assert rows[0].material_group == "stainless"


def test_load_csv_rows_supports_decimal_comma(tmp_path: Path) -> None:
    csv_path = _write_csv(
        tmp_path / "base_modes.csv",
        (
            "machine_name;material_group;gas_branch;thickness_mm;power;speed;frequency;"
            "pressure;focus;height;duty_cycle;nozzle\n"
            "LaserCell-3015;aluminum;N2;3,5;85;2,4;0;0,6;-0,5;0,8;100;1,2\n"
        ),
    )

    rows = load_csv_rows(csv_path)

    assert len(rows) == 1
    assert rows[0].thickness_mm == 3.5
    assert rows[0].speed_m_min == 2.4
    assert rows[0].pressure_bar == 0.6


def test_load_csv_rows_uses_default_trust_level_when_missing(tmp_path: Path) -> None:
    csv_path = _write_csv(
        tmp_path / "base_modes.csv",
        (
            "machine_name,material_group,gas_branch,thickness_mm,power,speed,frequency,"
            "pressure,focus,height,duty_cycle,nozzle\n"
            "LaserCell-3015,carbon,O2,3.0,85,2.4,0,0.8,-0.5,0.8,100,1.2\n"
        ),
    )

    rows = load_csv_rows(csv_path)

    assert len(rows) == 1
    assert rows[0].trust_level == DEFAULT_TRUST_LEVEL


def test_load_csv_rows_reads_trust_level_when_present(tmp_path: Path) -> None:
    csv_path = _write_csv(
        tmp_path / "base_modes.csv",
        (
            "machine_name,material_group,gas_branch,thickness_mm,power,speed,frequency,"
            "pressure,focus,height,duty_cycle,nozzle,trust_level,source_note\n"
            "LaserCell-3015,carbon,O2,3.0,85,2.4,0,0.8,-0.5,0.8,100,1.2,77,manual_measurement\n"
        ),
    )

    rows = load_csv_rows(csv_path)

    assert len(rows) == 1
    assert rows[0].trust_level == 77


def test_load_csv_rows_fails_when_trust_level_is_out_of_range(tmp_path: Path) -> None:
    csv_path = _write_csv(
        tmp_path / "base_modes.csv",
        (
            "machine_name,material_group,gas_branch,thickness_mm,power,speed,frequency,"
            "pressure,focus,height,duty_cycle,nozzle,trust_level\n"
            "LaserCell-3015,carbon,O2,3.0,85,2.4,0,0.8,-0.5,0.8,100,1.2,101\n"
        ),
    )

    with pytest.raises(BaseModesImportError, match="trust_level"):
        load_csv_rows(csv_path)


def test_upsert_base_modes_creates_missing_machine(sqlite_session_local) -> None:
    rows = [
        parse_csv_row(
            {
                "machine_name": "BrandNewMachine",
                "material_group": "carbon",
                "gas_branch": "O2",
                "thickness_mm": "4",
                "power": "88",
                "speed": "2.1",
                "frequency": "0",
                "pressure": "0.9",
                "focus": "-0.4",
                "height": "0.8",
                "duty_cycle": "100",
                "nozzle": "1.5",
            },
            2,
        )
    ]

    with sqlite_session_local() as db:
        db.add(Material(name="Carbon Steel", material_group="carbon", default_gas_branch="O2"))
        db.commit()

    imported_count = upsert_base_modes(rows)

    with sqlite_session_local() as db:
        machine = db.scalar(select(Machine).where(Machine.name == "BrandNewMachine"))

    assert imported_count == 1
    assert machine is not None
    assert machine.model == DEFAULT_MACHINE_MODEL
    assert machine.laser_power_w == DEFAULT_MACHINE_LASER_POWER_W
    assert machine.lens_focal_length_mm == DEFAULT_MACHINE_LENS_FOCAL_LENGTH_MM


def test_upsert_base_modes_creates_missing_material(sqlite_session_local) -> None:
    rows = [
        parse_csv_row(
            {
                "machine_name": "LaserCell-3015",
                "material_group": "titanium_alloy",
                "gas_branch": "HP",
                "thickness_mm": "2",
                "power": "72",
                "speed": "3.0",
                "frequency": "1200",
                "pressure": "10",
                "focus": "-0.2",
                "height": "0.7",
                "duty_cycle": "60",
                "nozzle": "1.2",
            },
            2,
        )
    ]

    with sqlite_session_local() as db:
        db.add(
            Machine(
                name="LaserCell-3015",
                model="LC",
                laser_power_w=6000,
                lens_focal_length_mm=125,
            )
        )
        db.commit()

    imported_count = upsert_base_modes(rows)

    with sqlite_session_local() as db:
        material = db.scalar(select(Material).where(Material.material_group == "titanium_alloy"))

    assert imported_count == 1
    assert material is not None
    assert material.name == "Titanium Alloy"
    assert material.default_gas_branch == "HP"


def test_upsert_base_modes_updates_existing_base_mode(sqlite_session_local) -> None:
    row = parse_csv_row(
            {
                "machine_name": "LaserCell-3015",
                "material_group": "carbon",
                "gas_branch": "O2",
            "thickness_mm": "3",
            "power": "90",
            "speed": "2.8",
            "frequency": "0",
            "pressure": "0.95",
            "focus": "-0.3",
            "height": "0.75",
            "duty_cycle": "100",
            "nozzle": "1.2",
        },
        2,
    )

    with sqlite_session_local() as db:
        material = Material(name="Carbon Steel", material_group="carbon", default_gas_branch="O2")
        machine = Machine(name="LaserCell-3015", model="LC", laser_power_w=6000, lens_focal_length_mm=125)
        db.add_all([material, machine])
        db.flush()
        db.add(
            BaseMode(
                material_id=material.id,
                machine_id=machine.id,
                thickness_mm=3.0,
                gas_type="O2",
                power_percent=70.0,
                speed_m_min=2.0,
                frequency_hz=0,
                pressure_bar=0.7,
                focus_mm=-0.6,
                cutting_height_mm=0.9,
                duty_cycle_percent=95,
                nozzle_diameter_mm=1.2,
                trust_level=50,
            )
        )
        db.commit()

    imported_count = upsert_base_modes([row])

    with sqlite_session_local() as db:
        modes = db.scalars(select(BaseMode)).all()

    assert imported_count == 1
    assert len(modes) == 1
    assert modes[0].power_percent == 90.0
    assert modes[0].speed_m_min == 2.8
    assert modes[0].trust_level == DEFAULT_TRUST_LEVEL


def test_upsert_base_modes_allows_ui_lookup_by_material_group_gas_and_thickness(
    sqlite_session_local,
) -> None:
    row = parse_csv_row(
        {
            "machine_name": "LaserCell-3015",
            "material_group": "carbon_steel",
            "gas_branch": "O2",
            "thickness_mm": "3",
            "power": "90",
            "speed": "2.8",
            "frequency": "0",
            "pressure": "0.95",
            "focus": "-0.3",
            "height": "0.75",
            "duty_cycle": "100",
            "nozzle": "1.2",
        },
        2,
    )

    imported_count = upsert_base_modes([row])

    with sqlite_session_local() as db:
        mode = db.scalar(
            select(BaseMode)
            .join(Material, BaseMode.material_id == Material.id)
            .where(
                Material.material_group == "carbon",
                BaseMode.gas_type == "O2",
                BaseMode.thickness_mm == 3.0,
            )
        )

    assert imported_count == 1
    assert mode is not None
