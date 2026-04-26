from datetime import datetime

from sqlalchemy import DateTime, Float, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CutSession(Base):
    __tablename__ = "cut_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    machine_name: Mapped[str] = mapped_column(String(255), nullable=False)
    material_group: Mapped[str] = mapped_column(String(255), nullable=False)
    thickness_mm: Mapped[float] = mapped_column(Float, nullable=False)
    gas_branch: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    iterations = relationship(
        "CutIteration", back_populates="session", cascade="all, delete-orphan"
    )
