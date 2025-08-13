from __future__ import annotations

"""User domain entity."""

from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import BigInteger, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .mixins import TimestampMixin
from .base import Base

if TYPE_CHECKING:
    from .fuel import Fuel
    from .language import Language
    from .search import Search

__all__ = ["User"]


class User(TimestampMixin, Base):
    """Application user identified by Telegram."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    tg_username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    fuel_id: Mapped[int] = mapped_column(ForeignKey("dom_fuels.id"), nullable=False)
    language_id: Mapped[Optional[int]] = mapped_column(ForeignKey("dom_languages.id"), nullable=True)

    # Relationships
    fuel: Mapped["Fuel"] = relationship(back_populates="users", lazy="joined")
    language: Mapped[Optional["Language"]] = relationship(back_populates="users", lazy="joined")
    searches: Mapped[List["Search"]] = relationship(back_populates="user", lazy="selectin")

    def __repr__(self) -> str:
        uname = self.tg_username
        if uname and len(uname) > 20:
            uname = uname[:20] + "…"
        return f"User(id={self.id}, tg_id={self.tg_id}, username={uname}, fuel_id={self.fuel_id}, lang_id={self.language_id})"
