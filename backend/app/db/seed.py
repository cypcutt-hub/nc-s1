from __future__ import annotations

from typing import TypedDict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models import AlgorithmStep, Defect, Material, Nozzle


class MaterialSeed(TypedDict):
    name: str
    material_group: str
    default_gas_branch: str


class DefectSeed(TypedDict):
    code: str
    name: str
    gas_branch: str
    is_critical: bool


class NozzleSeed(TypedDict):
    diameter_mm: float
    sort_order: int


class AlgorithmStepSeed(TypedDict):
    parameter_code: str
    severity_level: int
    step_value: float
    step_unit: str


MATERIALS_SEED: list[MaterialSeed] = [
    {"name": "Углеродистая сталь", "material_group": "carbon_steel", "default_gas_branch": "O2"},
    {"name": "Нержавеющая сталь", "material_group": "stainless_steel", "default_gas_branch": "HP"},
    {"name": "Алюминий", "material_group": "aluminum", "default_gas_branch": "HP"},
]

DEFECTS_SEED: list[DefectSeed] = [
    {"code": "burr", "name": "Грат", "gas_branch": "O2", "is_critical": False},
    {"code": "lag", "name": "Завал линий", "gas_branch": "O2", "is_critical": False},
    {"code": "rough_cut", "name": "Рваный рез", "gas_branch": "O2", "is_critical": False},
    {"code": "melting", "name": "Заплавление", "gas_branch": "O2", "is_critical": False},
    {"code": "no_cut", "name": "Непрорез", "gas_branch": "O2", "is_critical": True},
    {"code": "hp_burr", "name": "Грат HP", "gas_branch": "HP", "is_critical": False},
    {"code": "hp_roughness", "name": "Шероховатость HP", "gas_branch": "HP", "is_critical": False},
    {"code": "taper", "name": "Разный угол кромки", "gas_branch": "HP", "is_critical": False},
    {"code": "hp_no_cut", "name": "Непрорез HP", "gas_branch": "HP", "is_critical": True},
    {"code": "edge_overheat", "name": "Перегрев кромки", "gas_branch": "HP", "is_critical": False},
]

NOZZLES_SEED: list[NozzleSeed] = [
    {"diameter_mm": 1.0, "sort_order": 10},
    {"diameter_mm": 1.2, "sort_order": 12},
    {"diameter_mm": 1.5, "sort_order": 15},
    {"diameter_mm": 2.0, "sort_order": 20},
    {"diameter_mm": 2.5, "sort_order": 25},
    {"diameter_mm": 3.0, "sort_order": 30},
]

ALGORITHM_STEPS_SEED: list[AlgorithmStepSeed] = [
    {"parameter_code": "power_percent", "severity_level": 3, "step_value": 10.0, "step_unit": "%"},
    {"parameter_code": "power_percent", "severity_level": 2, "step_value": 5.0, "step_unit": "%"},
    {"parameter_code": "power_percent", "severity_level": 1, "step_value": 2.0, "step_unit": "%"},
    {"parameter_code": "speed_m_min", "severity_level": 3, "step_value": 10.0, "step_unit": "%"},
    {"parameter_code": "speed_m_min", "severity_level": 2, "step_value": 5.0, "step_unit": "%"},
    {"parameter_code": "speed_m_min", "severity_level": 1, "step_value": 2.0, "step_unit": "%"},
    {"parameter_code": "focus_mm", "severity_level": 3, "step_value": 0.7, "step_unit": "mm"},
    {"parameter_code": "focus_mm", "severity_level": 2, "step_value": 0.4, "step_unit": "mm"},
    {"parameter_code": "focus_mm", "severity_level": 1, "step_value": 0.2, "step_unit": "mm"},
    {"parameter_code": "pressure_bar", "severity_level": 3, "step_value": 0.1, "step_unit": "bar"},
    {"parameter_code": "pressure_bar", "severity_level": 2, "step_value": 0.05, "step_unit": "bar"},
    {"parameter_code": "pressure_bar", "severity_level": 1, "step_value": 0.02, "step_unit": "bar"},
    {"parameter_code": "cutting_height_mm", "severity_level": 3, "step_value": 0.2, "step_unit": "mm"},
    {"parameter_code": "cutting_height_mm", "severity_level": 2, "step_value": 0.1, "step_unit": "mm"},
    {"parameter_code": "cutting_height_mm", "severity_level": 1, "step_value": 0.05, "step_unit": "mm"},
    {"parameter_code": "frequency_hz", "severity_level": 3, "step_value": 1000.0, "step_unit": "Hz"},
    {"parameter_code": "frequency_hz", "severity_level": 2, "step_value": 500.0, "step_unit": "Hz"},
    {"parameter_code": "frequency_hz", "severity_level": 1, "step_value": 200.0, "step_unit": "Hz"},
    {"parameter_code": "duty_cycle_percent", "severity_level": 3, "step_value": 10.0, "step_unit": "%"},
    {"parameter_code": "duty_cycle_percent", "severity_level": 2, "step_value": 5.0, "step_unit": "%"},
    {"parameter_code": "duty_cycle_percent", "severity_level": 1, "step_value": 2.0, "step_unit": "%"},
]


def _seed_materials(db: Session) -> int:
    created = 0
    for row in MATERIALS_SEED:
        existing = db.scalar(select(Material).where(Material.material_group == row["material_group"]))
        if existing is None:
            db.add(Material(**row))
            created += 1
    return created


def _seed_defects(db: Session) -> int:
    created = 0
    for row in DEFECTS_SEED:
        existing = db.scalar(select(Defect).where(Defect.code == row["code"]))
        if existing is None:
            db.add(Defect(**row))
            created += 1
    return created


def _seed_nozzles(db: Session) -> int:
    created = 0
    for row in NOZZLES_SEED:
        existing = db.scalar(select(Nozzle).where(Nozzle.diameter_mm == row["diameter_mm"]))
        if existing is None:
            db.add(Nozzle(**row))
            created += 1
    return created


def _seed_algorithm_steps(db: Session) -> int:
    created = 0
    for row in ALGORITHM_STEPS_SEED:
        existing = db.scalar(
            select(AlgorithmStep).where(
                AlgorithmStep.parameter_code == row["parameter_code"],
                AlgorithmStep.severity_level == row["severity_level"],
            )
        )
        if existing is None:
            db.add(AlgorithmStep(**row))
            created += 1
    return created


def seed_reference_data() -> dict[str, int]:
    with SessionLocal() as db:
        stats = {
            "materials": _seed_materials(db),
            "defects": _seed_defects(db),
            "nozzles": _seed_nozzles(db),
            "algorithm_steps": _seed_algorithm_steps(db),
        }
        db.commit()
        return stats


def main() -> None:
    stats = seed_reference_data()
    print(
        "Seed completed: "
        f"materials={stats['materials']}, "
        f"defects={stats['defects']}, "
        f"nozzles={stats['nozzles']}, "
        f"algorithm_steps={stats['algorithm_steps']}"
    )


if __name__ == "__main__":
    main()
