from __future__ import annotations

"""Read-only view: geocoding call count in the last 30 days."""

from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column

from .base import ViewBase

__all__ = ["VGeocodingMonthCalls"]


class VGeocodingMonthCalls(ViewBase):
    """Maps the SQL view `v_geocoding_month_calls`."""

    __tablename__ = "v_geocoding_month_calls"
    __table_args__ = {"info": {"is_view": True}}

    count: Mapped[int] = mapped_column(Integer, primary_key=True)

    def __repr__(self) -> str:
        return f"VGeocodingMonthCalls(count={self.count})"
