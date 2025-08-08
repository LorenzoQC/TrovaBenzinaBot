from __future__ import annotations

"""Fuel domain entity."""

from decimal import Decimal
from typing import List, TYPE_CHECKING

from sqlalchemy import Numeric, String, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .mixins import CodeNameMixin, TimestampMixin

if TYPE_CHECKING:
    from .user import User
    from .search import Search

__all__ = ["Fuel"]


class Fuel(CodeNameMixin, TimestampMixin, Base):
    """Fuel type with unit of measure and average consumption."""

    __tablename__ = "dom_fuels"
    __table_args__ = (
        CheckConstraint("avg_consumption_per_100km > 0", name="ck_fuel_avg_cons_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    uom: Mapped[str] = mapped_column(String(15), nullable=False)
    avg_consumption_per_100km: Mapped[Decimal] = mapped_column(Numeric(6, 3), nullable=False)

    # Relationships
    users: Mapped[List["User"]] = relationship(back_populates="fuel", lazy="selectin")
    searches: Mapped[List["Search"]] = relationship(back_populates="fuel", lazy="selectin")

    def __repr__(self) -> str:
        return f"Fuel(id={self.id}, code={getattr(self, 'code', None)}, name={getattr(self, 'name', None)}, uom={self.uom})"
