from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    String,
    Float,
    ForeignKey,
    BigInteger,
    DateTime,
    func
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship
)


class TimestampMixin:
    """
    Mixin that adds timestamp fields to models:
    - ins_ts: insertion timestamp (default now)
    - upd_ts: update timestamp (auto-updated on change)
    - del_ts: deletion timestamp (nullable)
    """
    ins_ts: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    upd_ts: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), server_onupdate=func.now(), nullable=True
    )
    del_ts: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )


class CodeNameMixin:
    """
    Mixin that adds 'code' and 'name' fields for config tables.
    """
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


class Fuel(CodeNameMixin, TimestampMixin, Base):
    __tablename__ = "fuels"

    id: Mapped[int] = mapped_column(primary_key=True)

    users: Mapped[List["User"]] = relationship(back_populates="fuel")
    searches: Mapped[List["Search"]] = relationship(back_populates="fuel")


class Service(CodeNameMixin, TimestampMixin, Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(primary_key=True)

    users: Mapped[List["User"]] = relationship(back_populates="service")
    searches: Mapped[List["Search"]] = relationship(back_populates="service")


class Language(CodeNameMixin, TimestampMixin, Base):
    __tablename__ = "languages"

    id: Mapped[int] = mapped_column(primary_key=True)

    users: Mapped[List["User"]] = relationship(back_populates="language")


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    tg_username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    fuel_id: Mapped[int] = mapped_column(ForeignKey("fuels.id"), nullable=False)
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"), nullable=False)
    language_id: Mapped[int] = mapped_column(ForeignKey("languages.id"), nullable=True)

    fuel: Mapped[Fuel] = relationship(back_populates="users")
    service: Mapped[Service] = relationship(back_populates="users")
    language: Mapped[Language] = relationship(back_populates="users")

    searches: Mapped[List["Search"]] = relationship(back_populates="user")


class Search(TimestampMixin, Base):
    __tablename__ = "searches"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    fuel_id: Mapped[int] = mapped_column(ForeignKey("fuels.id"), nullable=False)
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"), nullable=False)

    price_avg: Mapped[float] = mapped_column(Float, nullable=False)
    price_min: Mapped[float] = mapped_column(Float, nullable=False)

    user: Mapped[User] = relationship(back_populates="searches")
    fuel: Mapped[Fuel] = relationship(back_populates="searches")
    service: Mapped[Service] = relationship(back_populates="searches")


class GeoCache(TimestampMixin, Base):
    __tablename__ = "geocache"

    id: Mapped[int] = mapped_column(primary_key=True)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    lat: Mapped[float] = mapped_column(nullable=False)
    lng: Mapped[float] = mapped_column(nullable=False)
