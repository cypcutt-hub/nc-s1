from app.db.base import Base
from app.models import BaseMode, Machine, Material  # noqa: F401


def test_models_import() -> None:
    assert Material is not None
    assert Machine is not None
    assert BaseMode is not None


def test_metadata_contains_expected_tables() -> None:
    assert "materials" in Base.metadata.tables
    assert "machines" in Base.metadata.tables
    assert "base_modes" in Base.metadata.tables
