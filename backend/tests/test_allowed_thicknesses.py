from pathlib import Path

import pytest

from app.services.allowed_thicknesses import AllowedThicknessesError
from app.services.allowed_thicknesses import (
    filter_allowed_thicknesses,
    load_allowed_thicknesses_csv,
)


CSV_PATH = Path(__file__).resolve().parents[1] / "data" / "allowed_thicknesses.csv"


def test_load_allowed_thicknesses_csv() -> None:
    rows = load_allowed_thicknesses_csv(CSV_PATH)

    assert len(rows) > 0
    first = rows[0]
    assert first.machine_power_w == 3000
    assert first.material_group
    assert isinstance(first.is_hot_block_zone, bool)


def test_filter_allowed_thicknesses_by_power_material_and_gas() -> None:
    rows = load_allowed_thicknesses_csv(CSV_PATH)

    filtered = filter_allowed_thicknesses(
        machine_power_w=3000,
        material_group="stainless",
        gas_branch="N2",
        rows=rows,
    )

    assert [item.thickness_mm for item in filtered] == [1, 2, 3, 4, 5, 6, 8, 10]


def test_hot_block_threshold_is_reflected_in_zone_flag() -> None:
    rows = load_allowed_thicknesses_csv(CSV_PATH)

    filtered = filter_allowed_thicknesses(
        machine_power_w=3000,
        material_group="carbon",
        gas_branch="O2",
        rows=rows,
    )

    threshold = filtered[0].hot_block_threshold_mm
    assert threshold == 11
    assert all(item.is_hot_block_zone == (item.thickness_mm >= threshold) for item in filtered)


@pytest.mark.parametrize("invalid_value", ["NaN", "inf", "-inf"])
def test_load_allowed_thicknesses_csv_rejects_non_finite_numbers(
    tmp_path: Path, invalid_value: str
) -> None:
    csv_path = tmp_path / "allowed_thicknesses.csv"
    csv_path.write_text(
        "\n".join(
            [
                "source_sheet,machine_power_w,material_group,gas_branch,thickness_mm,"
                "max_thickness_mm,hot_block_threshold_mm,is_hot_block_zone,source_gas_label",
                (
                    "sheet1,3000,stainless,N2,2,"
                    f"{invalid_value},8,false,Азот N2"
                ),
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(AllowedThicknessesError, match="must be a finite number"):
        load_allowed_thicknesses_csv(csv_path)
