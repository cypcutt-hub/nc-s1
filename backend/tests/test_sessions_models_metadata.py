from app.db.base import Base
from app.models import CutIteration, CutSession  # noqa: F401


def test_session_models_import() -> None:
    assert CutSession is not None
    assert CutIteration is not None


def test_metadata_contains_session_tables() -> None:
    assert "cut_sessions" in Base.metadata.tables
    assert "cut_iterations" in Base.metadata.tables
