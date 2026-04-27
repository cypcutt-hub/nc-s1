from pathlib import Path

import pytest

from app.db.import_base_modes import (
    BaseModesImportError,
    REQUIRED_COLUMNS,
    load_csv_rows,
    parse_csv_row,
)


def _write_csv(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


def test_parse_csv_row_accepts_valid_data() -> None:
    row = {
        "machine_name": "LaserCell-3015",
        "material_group": "carbon_steel",
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
    assert parsed.material_group == "carbon_steel"
    assert parsed.gas_branch == "O2"
    assert parsed.thickness_mm == 3.0
    assert parsed.nozzle_diameter_mm == 1.2


def test_load_csv_rows_fails_when_required_columns_are_missing(tmp_path: Path) -> None:
    csv_path = _write_csv(
        tmp_path / "base_modes.csv",
        "machine_name,material_group\nLaserCell-3015,carbon_steel\n",
    )

    with pytest.raises(BaseModesImportError, match="missing required columns"):
        load_csv_rows(csv_path)


def test_load_csv_rows_fails_for_invalid_numeric_field(tmp_path: Path) -> None:
    headers = ",".join(REQUIRED_COLUMNS)
    csv_path = _write_csv(
        tmp_path / "base_modes.csv",
        f"{headers}\nLaserCell-3015,carbon_steel,O2,not_a_number,85,2.4,0,0.8,-0.5,0.8,100,1.2\n",
    )

    with pytest.raises(BaseModesImportError, match="thickness_mm"):
        load_csv_rows(csv_path)
