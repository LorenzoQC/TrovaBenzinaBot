"""Read-only view: per-user, per-fuel aggregated search statistics."""

from decimal import Decimal

from sqlalchemy import Integer, String, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base

__all__ = ["VUsersSearchesStats"]


class VUsersSearchesStats(Base):
    """Maps the SQL view `v_users_searches_stats`."""

    __tablename__ = "v_users_searches_stats"
    __table_args__ = {"info": {"is_view": True}}

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fuel_id: Mapped[int] = mapped_column(Integer, primary_key=True)

    fuel_code: Mapped[str] = mapped_column(String)
    fuel_name: Mapped[str] = mapped_column(String)
    uom: Mapped[str] = mapped_column(String)

    avg_consumption_per_100km: Mapped[Decimal] = mapped_column(Numeric(6, 3))

    num_searches: Mapped[int] = mapped_column(Integer)
    num_stations: Mapped[int] = mapped_column(Integer)

    avg_eur_save_per_unit: Mapped[Decimal] = mapped_column(Numeric(10, 4))
    avg_pct_save: Mapped[Decimal] = mapped_column(Numeric(8, 4))
    estimated_annual_save_eur: Mapped[Decimal] = mapped_column(Numeric(12, 2))

    def __repr__(self) -> str:
        return (
            "VUsersSearchesStats("
            f"user_id={self.user_id}, fuel_id={self.fuel_id}, "
            f"num_searches={self.num_searches}, num_stations={self.num_stations})"
        )
