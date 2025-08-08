from __future__ import annotations

"""Language domain entity."""

from typing import List, TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .mixins import CodeNameMixin, TimestampMixin

if TYPE_CHECKING:
    from .user import User

__all__ = ["Language"]


class Language(CodeNameMixin, TimestampMixin, Base):
    """Language supported by the bot/UI."""

    __tablename__ = "dom_languages"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Relationships
    users: Mapped[List["User"]] = relationship(back_populates="language", lazy="selectin")

    def __repr__(self) -> str:
        return f"Language(id={self.id}, code={getattr(self, 'code', None)}, name={getattr(self, 'name', None)})"
