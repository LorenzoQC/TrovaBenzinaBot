"""Language repository: read helpers around the Language model."""

from typing import Dict, Optional

from sqlalchemy import select

from ..models import Language
from ..session import AsyncSession


async def get_language_map() -> Dict[str, str]:
    """Return a mapping of language names to language codes.

    Returns:
        Dict[str, str]: Mapping like {"Italiano": "it", "English": "en", ...}.
    """
    async with AsyncSession() as session:
        result = await session.execute(
            select(Language).where(Language.del_ts.is_(None))
        )
        languages = result.scalars().all()
    return {l.name: l.code for l in languages}


async def get_language_id_by_code(code: str) -> Optional[int]:
    """Resolve a language internal ID from its code.

    Args:
        code: Public `Language.code` (e.g., "it").

    Returns:
        Optional[int]: The internal `Language.id`, or raises if not found.

    Raises:
        sqlalchemy.exc.NoResultFound: If the code does not exist.
    """
    async with AsyncSession() as session:
        result = await session.execute(
            select(Language.id).where(Language.code == code)
        )
        return result.scalar_one()
