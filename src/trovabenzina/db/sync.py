import csv
import os
from datetime import datetime, timezone
from pathlib import Path

import aiofiles
import aiofiles.os
from sqlalchemy.future import select

from .models import Fuel, Language
from .session import AsyncSession

# Path to CSV folder
BASE_DIR = Path(__file__).resolve().parents[3]
ASSETS_CSV_DIR = BASE_DIR / "assets" / "config" / "csv"


async def _sync_model_from_csv(model, csv_filename):
    """
    Generic function to sync a model table with a CSV file.
    - Inserts records present in CSV but missing in DB.
    - Updates name if changed, and clears del_ts if previously soft-deleted.
    - Soft-deletes DB records no longer in CSV (sets del_ts to now).
    """
    csv_path = os.path.join(ASSETS_CSV_DIR, csv_filename)

    # Read CSV into a map: code -> full row dict
    async with aiofiles.open(csv_path, mode="r", encoding="utf-8") as f:
        await f.seek(0)
        content = await f.read()
    csv_map = {row["code"]: row for row in csv.DictReader(content.splitlines())}

    async with AsyncSession() as session:
        # Load existing items
        result = await session.execute(select(model))
        db_items = result.scalars().all()
        db_map = {item.code: item for item in db_items}
        now = datetime.now(timezone.utc)

        # 1) Insert new or update existing
        for code, row in csv_map.items():
            if code not in db_map:
                # build kwargs from CSV row (convert floats when possibile)
                kwargs = {"code": code}
                for key, val in row.items():
                    if key == "code":
                        continue
                    try:
                        parsed = float(val)
                    except (ValueError, TypeError):
                        parsed = val
                    kwargs[key] = parsed
                obj = model(**kwargs)
                session.add(obj)
            else:
                obj = db_map[code]
                # restore if soft-deleted
                if obj.del_ts is not None:
                    obj.del_ts = None
                # update fields if changed
                for key, val in row.items():
                    if key == "code" or not hasattr(obj, key):
                        continue
                    try:
                        parsed = float(val)
                    except (ValueError, TypeError):
                        parsed = val
                    if getattr(obj, key) != parsed:
                        setattr(obj, key, parsed)

        # 2) Soft-delete missing entries
        for code, obj in db_map.items():
            if code not in csv_map and obj.del_ts is None:
                obj.del_ts = now

        await session.commit()


async def sync_config_tables():
    """
    Sync languages and fuels tables with their respective CSV configs.
    """
    await _sync_model_from_csv(Fuel, "fuels.csv")
    await _sync_model_from_csv(Language, "languages.csv")
