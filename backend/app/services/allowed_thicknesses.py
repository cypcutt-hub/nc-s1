from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


REQUIRED_COLUMNS = (
    "source_sheet",
    "machine_power_w",
    "material_group",
    "gas_branch",
    "thickness_mm",
    "max_thickness_mm",
    "hot_block_threshold_mm",
    "is_hot_block_zone",
    "source_gas_label",
)

CSV_PATH = Path(__file__).resolve().parents[2] / "data" / "allowed_thicknesses.csv"


class AllowedThicknessesError(ValueError):
    """Raised when allowed thickness CSV is invalid."""


@dataclass(frozen=True)
class AllowedThicknessRow:
    source_sheet: str
    machine_power_w: int
    material_group: str
    gas_branch: str
    thickness_mm: float
    max_thickness_mm: float
    hot_block_threshold_mm: float
    is_hot_block_zone: bool
    source_gas_label: str


def _as_text(value: str | None, column: str, row_number: int) -> str:
    text = (value or "").strip()
    if not text:
        raise AllowedThicknessesError(f"Row {row_number}: '{column}' is required")
    return text


def _as_float(value: str | None, column: str, row_number: int) -> float:
    text = _as_text(value, column, row_number)
    normalized = text.replace(",", ".")
    try:
        parsed = float(normalized)
    except ValueError as exc:
        raise AllowedThicknessesError(
            f"Row {row_number}: '{column}' must be numeric, got '{text}'"
        ) from exc

    if not math.isfinite(parsed):
        raise AllowedThicknessesError(
            f"Row {row_number}: '{column}' must be a finite number, got '{text}'"
        )

    return parsed


def _as_int(value: str | None, column: str, row_number: int) -> int:
    text = _as_text(value, column, row_number)
    try:
        return int(text)
    except ValueError as exc:
        raise AllowedThicknessesError(
            f"Row {row_number}: '{column}' must be an integer, got '{text}'"
        ) from exc


def _as_bool(value: str | None, column: str, row_number: int) -> bool:
    text = _as_text(value, column, row_number).lower()
    if text in {"true", "1", "yes"}:
        return True
    if text in {"false", "0", "no"}:
        return False
    raise AllowedThicknessesError(
        f"Row {row_number}: '{column}' must be boolean true/false, got '{text}'"
    )


@lru_cache(maxsize=1)
def load_allowed_thicknesses_csv(csv_path: Path = CSV_PATH) -> tuple[AllowedThicknessRow, ...]:
    if not csv_path.exists():
        raise AllowedThicknessesError(f"CSV file not found: {csv_path}")

    with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames is None:
            raise AllowedThicknessesError("CSV file is empty or missing header")

        missing_columns = [column for column in REQUIRED_COLUMNS if column not in reader.fieldnames]
        if missing_columns:
            raise AllowedThicknessesError(
                "CSV is missing required columns: " + ", ".join(sorted(missing_columns))
            )

        rows: list[AllowedThicknessRow] = []
        for index, row in enumerate(reader, start=2):
            rows.append(
                AllowedThicknessRow(
                    source_sheet=_as_text(row.get("source_sheet"), "source_sheet", index),
                    machine_power_w=_as_int(row.get("machine_power_w"), "machine_power_w", index),
                    material_group=_as_text(row.get("material_group"), "material_group", index),
                    gas_branch=_as_text(row.get("gas_branch"), "gas_branch", index),
                    thickness_mm=_as_float(row.get("thickness_mm"), "thickness_mm", index),
                    max_thickness_mm=_as_float(row.get("max_thickness_mm"), "max_thickness_mm", index),
                    hot_block_threshold_mm=_as_float(
                        row.get("hot_block_threshold_mm"), "hot_block_threshold_mm", index
                    ),
                    is_hot_block_zone=_as_bool(
                        row.get("is_hot_block_zone"), "is_hot_block_zone", index
                    ),
                    source_gas_label=_as_text(row.get("source_gas_label"), "source_gas_label", index),
                )
            )

    return tuple(rows)


def filter_allowed_thicknesses(
    machine_power_w: int,
    material_group: str,
    gas_branch: str,
    rows: tuple[AllowedThicknessRow, ...] | None = None,
) -> list[AllowedThicknessRow]:
    source_rows = rows if rows is not None else load_allowed_thicknesses_csv()

    filtered = [
        row
        for row in source_rows
        if row.machine_power_w == machine_power_w
        and row.material_group == material_group
        and row.gas_branch == gas_branch
    ]
    filtered.sort(key=lambda row: row.thickness_mm)
    return filtered
