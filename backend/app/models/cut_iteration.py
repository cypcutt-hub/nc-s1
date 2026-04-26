from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CutIteration(Base):
    __tablename__ = "cut_iterations"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("cut_sessions.id"), nullable=False)
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)
    defect_code: Mapped[str] = mapped_column(String(255), ForeignKey("defects.code"), nullable=False)
    severity_level: Mapped[int] = mapped_column(Integer, nullable=False)

    power_before: Mapped[float] = mapped_column(Float, nullable=False)
    speed_before: Mapped[float] = mapped_column(Float, nullable=False)
    frequency_before: Mapped[float] = mapped_column(Float, nullable=False)
    focus_before: Mapped[float] = mapped_column(Float, nullable=False)
    pressure_before: Mapped[float] = mapped_column(Float, nullable=False)
    height_before: Mapped[float] = mapped_column(Float, nullable=False)
    duty_cycle_before: Mapped[float] = mapped_column(Float, nullable=False)
    nozzle_before: Mapped[float] = mapped_column(Float, nullable=False)

    power_after: Mapped[float] = mapped_column(Float, nullable=False)
    speed_after: Mapped[float] = mapped_column(Float, nullable=False)
    frequency_after: Mapped[float] = mapped_column(Float, nullable=False)
    focus_after: Mapped[float] = mapped_column(Float, nullable=False)
    pressure_after: Mapped[float] = mapped_column(Float, nullable=False)
    height_after: Mapped[float] = mapped_column(Float, nullable=False)
    duty_cycle_after: Mapped[float] = mapped_column(Float, nullable=False)
    nozzle_after: Mapped[float] = mapped_column(Float, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    session = relationship("CutSession", back_populates="iterations")
