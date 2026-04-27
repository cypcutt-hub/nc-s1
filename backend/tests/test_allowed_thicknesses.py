from pathlib import Path

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
