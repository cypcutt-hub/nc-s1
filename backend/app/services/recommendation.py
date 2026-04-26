from app.models import CutIteration, CutSession
from app.schemas import RecommendationRead

SEVERITY_MULTIPLIERS = {
    1: 1.0,
    2: 1.5,
    3: 2.0,
}

DEFECT_RULES = {
    "no_cut": {"power_after": 5.0, "speed_after": -5.0},
    "burr": {"power_after": -5.0, "speed_after": 5.0},
    "overburn": {"power_after": -10.0},
}


def _power_context_multiplier(session: CutSession) -> float:
    multiplier = 1.0
    gas_branch = session.gas_branch.strip().upper()
    material_group = session.material_group.strip().lower()

    if session.thickness_mm > 5:
        multiplier *= 1.5
    elif session.thickness_mm < 2:
        multiplier *= 0.7

    if gas_branch == "O2":
        multiplier *= 1.3

    if material_group == "stainless":
        multiplier *= 0.8
    elif material_group == "carbon":
        multiplier *= 1.1

    return multiplier


def _speed_context_multiplier(session: CutSession) -> float:
    multiplier = 1.0
    gas_branch = session.gas_branch.strip().upper()

    if session.thickness_mm > 5:
        multiplier *= 0.8

    if gas_branch == "N2":
        multiplier *= 1.2

    return multiplier


def _context_multiplier(field_name: str, session: CutSession) -> float:
    if field_name == "power_after":
        return _power_context_multiplier(session)
    if field_name == "speed_after":
        return _speed_context_multiplier(session)
    return 1.0


def build_recommendation_from_iteration(
    iteration: CutIteration, session: CutSession
) -> RecommendationRead:
    severity_multiplier = SEVERITY_MULTIPLIERS.get(iteration.severity_level, 1.0)
    adjustments = DEFECT_RULES.get(iteration.defect_code, {})
    explanation: list[str] = []

    recommended_values = {
        "power_after": iteration.power_after,
        "speed_after": iteration.speed_after,
        "frequency_after": iteration.frequency_after,
        "pressure_after": iteration.pressure_after,
        "focus_after": iteration.focus_after,
        "height_after": iteration.height_after,
        "duty_cycle_after": iteration.duty_cycle_after,
        "nozzle_after": iteration.nozzle_after,
    }

    if adjustments:
        adjustment_parts = []
        if "power_after" in adjustments:
            power_direction = "increase" if adjustments["power_after"] > 0 else "decrease"
            adjustment_parts.append(f"{power_direction} power")
        if "speed_after" in adjustments:
            speed_direction = "increase" if adjustments["speed_after"] > 0 else "decrease"
            adjustment_parts.append(f"{speed_direction} speed")
        explanation.append(
            f"Base rule for {iteration.defect_code}: {', '.join(adjustment_parts)}"
        )

    explanation.append(
        f"Severity level {iteration.severity_level} applied multiplier x{severity_multiplier:g}"
    )

    if session.thickness_mm > 5:
        explanation.append(
            f"Thickness {session.thickness_mm:.1f} mm increased power impact and reduced speed impact"
        )
    elif session.thickness_mm < 2:
        explanation.append(
            f"Thickness {session.thickness_mm:.1f} mm reduced power impact"
        )

    gas_branch = session.gas_branch.strip().upper()
    if gas_branch == "O2":
        explanation.append("Gas O2 amplified power changes")
    elif gas_branch == "N2":
        explanation.append("Gas N2 increased speed sensitivity")

    material_group = session.material_group.strip().lower()
    if material_group == "carbon":
        explanation.append("Material carbon increased power sensitivity")
    elif material_group == "stainless":
        explanation.append("Material stainless reduced power sensitivity")

    for field_name, base_delta in adjustments.items():
        base_value = recommended_values[field_name]
        context_multiplier = _context_multiplier(field_name, session)
        final_delta = base_delta * severity_multiplier * context_multiplier
        adjusted_value = base_value * (1 + final_delta / 100.0)
        recommended_values[field_name] = adjusted_value

    return RecommendationRead(**recommended_values, explanation=explanation)
