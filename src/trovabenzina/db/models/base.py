"""Declarative base for all ORM models."""

from sqlalchemy.orm import DeclarativeBase

__all__ = ["Base"]


class Base(DeclarativeBase):
    """Declarative base class used by all mapped classes."""
    pass
