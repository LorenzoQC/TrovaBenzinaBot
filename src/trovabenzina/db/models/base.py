"""Declarative base for all ORM models."""

from sqlalchemy.orm import DeclarativeBase

__all__ = ["Base", "ViewBase"]


class Base(DeclarativeBase):
    """Declarative base class used by all mapped table classes."""
    pass


class ViewBase(DeclarativeBase):
    """Declarative base for models mapped to database views (read-only).

    These models must NOT be included in `Base.metadata.create_all()`.
    """
    pass
