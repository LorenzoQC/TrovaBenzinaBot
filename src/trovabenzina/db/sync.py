import csv
import os
from datetime import datetime, timezone

import aiofiles
import aiofiles.os
from sqlalchemy.future import select

from .models import Fuel, Service, Language
from .session import AsyncSession

# Path to CSV folder
ASSETS_CONFIG_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../../assets/config")
)


async def _sync_model_from_csv(model, csv_filename):
    """
    Generic function to sync a model table with a CSV file.
    - Inserts records present in CSV but missing in DB.
    - Updates name if changed, and clears del_ts if previously soft-deleted.
    - Soft-deletes DB records no longer in CSV (sets del_ts to now).
    """
    csv_path = os.path.join(ASSETS_CONFIG_DIR, csv_filename)

    # Read CSV asynchronously
    async with aiofiles.open(csv_path, mode="r", encoding="utf-8") as f:
        # Reset pointer and read all lines
        await f.seek(0)
        lines = await f.read()
    csv_map = {}
    for row in csv.DictReader(lines.splitlines()):
        # Expect columns: code, name
        csv_map[row["code"]] = row["name"]

    async with AsyncSession() as session:
        result = await session.execute(select(model))
        db_items = result.scalars().all()

        now = datetime.now(timezone.utc)
        db_map = {item.code: item for item in db_items}

        # 1) Insert new or update existing
        for code, name in csv_map.items():
            if code not in db_map:
                obj = model(code=code, name=name)
                session.add(obj)
            else:
                obj = db_map[code]
                # Restore if soft-deleted
                if obj.del_ts is not None:
                    obj.del_ts = None
                # Update name if changed
                if obj.name != name:
                    obj.name = name

        # 2) Soft-delete missing entries
        for code, obj in db_map.items():
            if code not in csv_map and obj.del_ts is None:
                obj.del_ts = now

        await session.commit()


async def sync_config_tables():
    """
    Sync fuels, services, and languages tables with their respective CSV configs.
    """
    await _sync_model_from_csv(Fuel, "fuels.csv")
    await _sync_model_from_csv(Service, "services.csv")
    await _sync_model_from_csv(Language, "languages.csv")
