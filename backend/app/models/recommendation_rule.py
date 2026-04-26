from sqlalchemy import Boolean, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RecommendationRule(Base):
    __tablename__ = "recommendation_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    defect_code: Mapped[str] = mapped_column(String(255), nullable=False)
    parameter: Mapped[str] = mapped_column(String(64), nullable=False)
    direction: Mapped[str] = mapped_column(String(16), nullable=False)
    base_delta: Mapped[float] = mapped_column(Float, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
