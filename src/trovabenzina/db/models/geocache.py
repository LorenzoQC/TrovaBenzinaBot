"""Cache of geocoding results."""

from decimal import Decimal

from sqlalchemy import String, Numeric, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base
from .mixins import TimestampMixin

__all__ = ["GeoCache"]


class GeoCache(TimestampMixin, Base):
    """Stores resolved coordinates for an address."""

    __tablename__ = "geocache"
    __table_args__ = (
        CheckConstraint("lat >= -90 AND lat <= 90", name="ck_geocache_lat_range"),
        CheckConstraint("lng >= -180 AND lng <= 180", name="ck_geocache_lng_range"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    # Precise numeric for coordinates
    lat: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    lng: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)

    def __repr__(self) -> str:
        return f"GeoCache(id={self.id}, address={self.address}, lat={self.lat}, lng={self.lng})"
