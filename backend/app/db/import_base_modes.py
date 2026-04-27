from __future__ import annotations

import csv
import sys
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models import BaseMode, Machine, Material

REQUIRED_COLUMNS = (
    "machine_name",
    "material_group",
    "gas_branch",
    "thickness_mm",
    "power",
    "speed",
    "frequency",
    "pressure",
    "focus",
    "height",
    "duty_cycle",
    "nozzle",
)

DEFAULT_TRUST_LEVEL = 100
DEFAULT_MACHINE_MODEL = "auto-imported"
DEFAULT_MACHINE_LASER_POWER_W = 6000
DEFAULT_MACHINE_LENS_FOCAL_LENGTH_MM = 125


class BaseModesImportError(ValueError):
    """Raised when CSV import data is invalid."""


@dataclass
class ParsedBaseModeRow:
    machine_name: str
    material_group: str
    gas_branch: str
    thickness_mm: float
    power_percent: float
    speed_m_min: float
    frequency_hz: float | None
    pressure_bar: float
    focus_mm: float
    cutting_height_mm: float
    duty_cycle_percent: float | None
    nozzle_diameter_mm: float
    trust_level: int


MATERIAL_GROUP_ALIASES = {
    "carbon_steel": "carbon",
    "stainless_steel": "stainless",
}


def _as_required_text(value: str | None, column: str, row_number: int) -> str:
    text = (value or "").strip()
    if not text:
        raise BaseModesImportError(f"Row {row_number}: '{column}' is required")
    return text


def _as_float(value: str | None, column: str, row_number: int, *, allow_empty: bool = False) -> float | None:
    text = (value or "").strip()
    if not text:
        if allow_empty:
            return None
        raise BaseModesImportError(f"Row {row_number}: '{column}' is required")

    normalized = text.replace(",", ".")

    try:
        return float(normalized)
    except ValueError as exc:
        raise BaseModesImportError(f"Row {row_number}: '{column}' must be numeric, got '{text}'") from exc


def _as_trust_level(value: str | None, row_number: int) -> int:
    text = (value or "").strip()
    if not text:
        return DEFAULT_TRUST_LEVEL

    try:
        trust_level = int(text)
    except ValueError as exc:
        raise BaseModesImportError(
            f"Row {row_number}: 'trust_level' must be an integer between 1 and 100, got '{text}'"
        ) from exc

    if trust_level < 1 or trust_level > 100:
        raise BaseModesImportError(
            f"Row {row_number}: 'trust_level' must be in range 1..100, got '{trust_level}'"
        )
    return trust_level


def _normalize_material_group(material_group: str) -> str:
    return MATERIAL_GROUP_ALIASES.get(material_group.strip().lower(), material_group.strip().lower())


def parse_csv_row(row: dict[str, str], row_number: int) -> ParsedBaseModeRow:
    return ParsedBaseModeRow(
        machine_name=_as_required_text(row.get("machine_name"), "machine_name", row_number),
        material_group=_normalize_material_group(
            _as_required_text(row.get("material_group"), "material_group", row_number)
        ),
        gas_branch=_as_required_text(row.get("gas_branch"), "gas_branch", row_number),
        thickness_mm=float(_as_float(row.get("thickness_mm"), "thickness_mm", row_number)),
        power_percent=float(_as_float(row.get("power"), "power", row_number)),
        speed_m_min=float(_as_float(row.get("speed"), "speed", row_number)),
        frequency_hz=_as_float(row.get("frequency"), "frequency", row_number, allow_empty=True),
        pressure_bar=float(_as_float(row.get("pressure"), "pressure", row_number)),
        focus_mm=float(_as_float(row.get("focus"), "focus", row_number)),
        cutting_height_mm=float(_as_float(row.get("height"), "height", row_number)),
        duty_cycle_percent=_as_float(row.get("duty_cycle"), "duty_cycle", row_number, allow_empty=True),
        nozzle_diameter_mm=float(_as_float(row.get("nozzle"), "nozzle", row_number)),
        trust_level=_as_trust_level(row.get("trust_level"), row_number),
    )


def load_csv_rows(csv_path: Path) -> list[ParsedBaseModeRow]:
    if not csv_path.exists():
        raise BaseModesImportError(f"CSV file not found: {csv_path}")

    with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
        sample = file.read(4096)
        file.seek(0)

        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;")
            delimiter = dialect.delimiter
        except csv.Error:
            delimiter = ","

        reader = csv.DictReader(file, delimiter=delimiter)
        if reader.fieldnames is None:
            raise BaseModesImportError("CSV file is empty or missing header")

        missing_columns = [column for column in REQUIRED_COLUMNS if column not in reader.fieldnames]
        if missing_columns:
            raise BaseModesImportError(
                "CSV is missing required columns: " + ", ".join(sorted(missing_columns))
            )

        parsed_rows: list[ParsedBaseModeRow] = []
        for index, row in enumerate(reader, start=2):
            parsed_rows.append(parse_csv_row(row, index))

    return parsed_rows


def _get_or_create_machine(db: Session, machine_name: str) -> Machine:
    machine = db.scalar(select(Machine).where(Machine.name == machine_name))
    if machine is None:
        machine = Machine(
            name=machine_name,
            model=DEFAULT_MACHINE_MODEL,
            laser_power_w=DEFAULT_MACHINE_LASER_POWER_W,
            lens_focal_length_mm=DEFAULT_MACHINE_LENS_FOCAL_LENGTH_MM,
        )
        db.add(machine)
        db.flush()
    return machine


def _get_or_create_material(db: Session, material_group: str, gas_branch: str) -> Material:
    material = db.scalar(select(Material).where(Material.material_group == material_group))
    if material is None:
        readable_name = material_group.replace("_", " ").title()
        material = Material(
            name=readable_name,
            material_group=material_group,
            default_gas_branch=gas_branch,
        )
        db.add(material)
        db.flush()
    return material


def upsert_base_modes(rows: list[ParsedBaseModeRow]) -> int:
    imported_count = 0

    with SessionLocal() as db:
        for row in rows:
            machine = _get_or_create_machine(db, row.machine_name)
            material = _get_or_create_material(db, row.material_group, row.gas_branch)

            existing = db.scalar(
                select(BaseMode).where(
                    BaseMode.machine_id == machine.id,
                    BaseMode.material_id == material.id,
                    BaseMode.gas_type == row.gas_branch,
                    BaseMode.thickness_mm == row.thickness_mm,
                    BaseMode.nozzle_diameter_mm == row.nozzle_diameter_mm,
                )
            )

            values = {
                "material_id": material.id,
                "machine_id": machine.id,
                "thickness_mm": row.thickness_mm,
                "gas_type": row.gas_branch,
                "power_percent": row.power_percent,
                "speed_m_min": row.speed_m_min,
                "frequency_hz": row.frequency_hz,
                "pressure_bar": row.pressure_bar,
                "focus_mm": row.focus_mm,
                "cutting_height_mm": row.cutting_height_mm,
                "duty_cycle_percent": row.duty_cycle_percent,
                "nozzle_diameter_mm": row.nozzle_diameter_mm,
                "trust_level": row.trust_level,
            }

            if existing is None:
                db.add(BaseMode(**values))
            else:
                for key, value in values.items():
                    setattr(existing, key, value)

            imported_count += 1

        db.commit()

    return imported_count


def import_base_modes(csv_path: Path) -> int:
    rows = load_csv_rows(csv_path)
    return upsert_base_modes(rows)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python -m app.db.import_base_modes <path_to_csv>")

    csv_path = Path(sys.argv[1])

    try:
        imported_count = import_base_modes(csv_path)
    except BaseModesImportError as exc:
        raise SystemExit(f"Base modes import failed: {exc}") from exc

    print(f"Imported {imported_count} base mode rows")


if __name__ == "__main__":
    main()
