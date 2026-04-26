from app.db.base import Base
from app.models import AlgorithmStep, Defect, Nozzle  # noqa: F401


def test_reference_models_import() -> None:
    assert Defect is not None
    assert Nozzle is not None
    assert AlgorithmStep is not None


def test_metadata_contains_reference_tables() -> None:
    assert "defects" in Base.metadata.tables
    assert "nozzles" in Base.metadata.tables
    assert "algorithm_steps" in Base.metadata.tables
