from app.db.seed import ALGORITHM_STEPS_SEED, DEFECTS_SEED, MATERIALS_SEED, NOZZLES_SEED


def test_seed_data_importable() -> None:
    assert MATERIALS_SEED is not None
    assert DEFECTS_SEED is not None
    assert NOZZLES_SEED is not None
    assert ALGORITHM_STEPS_SEED is not None


def test_seed_lists_not_empty() -> None:
    assert len(MATERIALS_SEED) > 0
    assert len(DEFECTS_SEED) > 0
    assert len(NOZZLES_SEED) > 0
    assert len(ALGORITHM_STEPS_SEED) > 0


def test_focus_mm_has_three_steps() -> None:
    focus_steps = [step for step in ALGORITHM_STEPS_SEED if step["parameter_code"] == "focus_mm"]

    assert len(focus_steps) == 3
    assert {step["severity_level"] for step in focus_steps} == {1, 2, 3}


def test_no_cut_defect_is_critical() -> None:
    no_cut_defect = next(defect for defect in DEFECTS_SEED if defect["code"] == "no_cut")

    assert no_cut_defect["is_critical"] is True
