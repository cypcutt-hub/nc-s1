from datetime import datetime

from sqlalchemy import DateTime, Float, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AlgorithmStep(Base):
    __tablename__ = "algorithm_steps"
    __table_args__ = (UniqueConstraint("parameter_code", "severity_level"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    parameter_code: Mapped[str] = mapped_column(String(255), nullable=False)
    severity_level: Mapped[str] = mapped_column(String(255), nullable=False)
    step_value: Mapped[float] = mapped_column(Float, nullable=False)
    step_unit: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
