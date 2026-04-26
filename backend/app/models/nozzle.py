from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Nozzle(Base):
    __tablename__ = "nozzles"

    id: Mapped[int] = mapped_column(primary_key=True)
    diameter_mm: Mapped[float] = mapped_column(Float, nullable=False, unique=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
