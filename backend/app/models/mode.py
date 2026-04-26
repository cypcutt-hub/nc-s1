from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class BaseMode(Base):
    __tablename__ = "base_modes"

    id: Mapped[int] = mapped_column(primary_key=True)
    material_id: Mapped[int] = mapped_column(ForeignKey("materials.id"), nullable=False)
    machine_id: Mapped[Optional[int]] = mapped_column(ForeignKey("machines.id"), nullable=True)
    thickness_mm: Mapped[float] = mapped_column(Float, nullable=False)
    gas_type: Mapped[str] = mapped_column(nullable=False)
    power_percent: Mapped[float] = mapped_column(Float, nullable=False)
    speed_m_min: Mapped[float] = mapped_column(Float, nullable=False)
    frequency_hz: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pressure_bar: Mapped[float] = mapped_column(Float, nullable=False)
    focus_mm: Mapped[float] = mapped_column(Float, nullable=False)
    cutting_height_mm: Mapped[float] = mapped_column(Float, nullable=False)
    duty_cycle_percent: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    nozzle_diameter_mm: Mapped[float] = mapped_column(Float, nullable=False)
    trust_level: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    material = relationship("Material", back_populates="base_modes")
    machine = relationship("Machine", back_populates="base_modes")
