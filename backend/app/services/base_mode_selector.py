from __future__ import annotations

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import BaseMode, Machine, Material


def _select_highest_trust_mode(modes: list[BaseMode]) -> BaseMode:
    return sorted(modes, key=lambda mode: (-mode.trust_level, mode.id))[0]


def _interpolate_value(lower: float, upper: float, ratio: float) -> float:
    return lower + (upper - lower) * ratio


def _build_interpolated_mode(
    target_thickness: float, lower_mode: BaseMode, upper_mode: BaseMode
) -> BaseMode:
    ratio = (target_thickness - lower_mode.thickness_mm) / (
        upper_mode.thickness_mm - lower_mode.thickness_mm
    )

    reference_mode = lower_mode
    if abs(target_thickness - upper_mode.thickness_mm) < abs(
        target_thickness - lower_mode.thickness_mm
    ):
        reference_mode = upper_mode

    return BaseMode(
        material_id=reference_mode.material_id,
        machine_id=reference_mode.machine_id,
        thickness_mm=target_thickness,
        gas_type=reference_mode.gas_type,
        power_percent=reference_mode.power_percent,
        speed_m_min=_interpolate_value(
            lower_mode.speed_m_min, upper_mode.speed_m_min, ratio
        ),
        frequency_hz=reference_mode.frequency_hz,
        pressure_bar=_interpolate_value(
            lower_mode.pressure_bar, upper_mode.pressure_bar, ratio
        ),
        focus_mm=_interpolate_value(lower_mode.focus_mm, upper_mode.focus_mm, ratio),
        cutting_height_mm=_interpolate_value(
            lower_mode.cutting_height_mm, upper_mode.cutting_height_mm, ratio
        ),
        duty_cycle_percent=reference_mode.duty_cycle_percent,
        nozzle_diameter_mm=reference_mode.nozzle_diameter_mm,
        trust_level=min(lower_mode.trust_level, upper_mode.trust_level),
    )


def get_best_base_mode(
    machine_name: str,
    material_group: str,
    gas_branch: str,
    thickness_mm: float,
) -> BaseMode | None:
    with SessionLocal() as db:
        matching_modes = db.scalars(
            select(BaseMode)
            .join(Machine, BaseMode.machine_id == Machine.id)
            .join(Material, BaseMode.material_id == Material.id)
            .where(
                Machine.name == machine_name,
                Material.material_group == material_group,
                BaseMode.gas_type == gas_branch,
            )
        ).all()

    if not matching_modes:
        return None

    modes_by_thickness: dict[float, list[BaseMode]] = {}
    for mode in matching_modes:
        modes_by_thickness.setdefault(mode.thickness_mm, []).append(mode)

    preferred_by_thickness = {
        thickness: _select_highest_trust_mode(modes)
        for thickness, modes in modes_by_thickness.items()
    }

    exact_mode = preferred_by_thickness.get(thickness_mm)
    if exact_mode is not None:
        return exact_mode

    sorted_thicknesses = sorted(preferred_by_thickness.keys())
    lower = [value for value in sorted_thicknesses if value < thickness_mm]
    upper = [value for value in sorted_thicknesses if value > thickness_mm]

    lower_mode = preferred_by_thickness[lower[-1]] if lower else None
    upper_mode = preferred_by_thickness[upper[0]] if upper else None

    if lower_mode is not None and upper_mode is not None:
        return _build_interpolated_mode(thickness_mm, lower_mode, upper_mode)

    if lower_mode is not None:
        return lower_mode
    if upper_mode is not None:
        return upper_mode

    return None
