from app.models import CutIteration
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


def build_recommendation_from_iteration(iteration: CutIteration) -> RecommendationRead:
    multiplier = SEVERITY_MULTIPLIERS.get(iteration.severity_level, 1.0)
    adjustments = DEFECT_RULES.get(iteration.defect_code, {})

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

    for field_name, percent_delta in adjustments.items():
        base_value = recommended_values[field_name]
        adjusted_value = base_value * (1 + (percent_delta / 100.0) * multiplier)
        recommended_values[field_name] = adjusted_value

    return RecommendationRead(**recommended_values)
