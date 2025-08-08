"""Common mixins for timestamps and (code, name) fields."""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

__all__ = ["TimestampMixin", "CodeNameMixin"]


class TimestampMixin:
    """Adds soft-delete friendly timestamps.

    Attributes:
        ins_ts: Insertion timestamp, set by the DB server (`now()`).
        upd_ts: Update timestamp, auto-updated by the DB on row modification.
        del_ts: Deletion timestamp; `NULL` means row is active (soft-delete).
    """

    ins_ts: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    upd_ts: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )
    del_ts: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )


class CodeNameMixin:
    """Adds a unique code and a human-readable name.

    Attributes:
        code: Stable unique code used in APIs and FKs (indexed).
        name: Human-readable display name.
    """

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
