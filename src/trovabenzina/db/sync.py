from __future__ import annotations

"""
Config-table synchronization utilities.

Reads CSV assets (e.g., fuels, languages) and synchronizes them into the DB.
Performs idempotent upserts based on the `code` column and soft-deletes rows
missing from the CSV by setting `del_ts`.
"""

import csv
import logging
import os
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import aiofiles
from sqlalchemy import Boolean, DateTime, Float, Integer, Numeric, String, select

from .models import Fuel, Language
from .session import AsyncSession

log = logging.getLogger(__name__)

# Paths to CSV assets
BASE_DIR = Path(__file__).resolve().parents[3]
ASSETS_CSV_DIR = BASE_DIR / "assets" / "config" / "csv"


# ---------- helpers: typing-aware casting & comparison ----------

def _as_bool(val: str) -> bool:
    """Parse common textual booleans."""
    v = (val or "").strip().lower()
    return v in {"1", "true", "t", "yes", "y", "on"}


def _cast_for_column(col_type, raw: Optional[str]) -> Any:
    """Cast CSV string to a Python value matching the SQLAlchemy column type.

    For Numeric -> Decimal; Integer -> int; Float -> float; Boolean -> bool;
    DateTime is left as-is (not expected here); String -> original string.

    Empty strings are turned into None.
    """
    if raw is None:
        return None
    if isinstance(raw, str) and raw.strip() == "":
        return None

    try:
        if isinstance(col_type, Numeric):
            # Use Decimal for exact precision; rely on DB scale/rounding rules.
            return Decimal(str(raw))
        if isinstance(col_type, Integer):
            return int(raw)
        if isinstance(col_type, Float):
            return float(raw)
        if isinstance(col_type, Boolean):
            return _as_bool(str(raw))
        if isinstance(col_type, DateTime):
            # Expect ISO8601 or a format handled elsewhere; keep raw string by default.
            return raw
        if isinstance(col_type, String):
            return str(raw)
    except (ValueError, TypeError, InvalidOperation):
        # Fallback: return the raw value to avoid hard failures during sync.
        log.warning("Failed to cast value '%s' for type %s; keeping raw.", raw, type(col_type).__name__)
        return raw

    # Default: return raw as string
    return raw


def _model_columns_map(model) -> Dict[str, Any]:
    """Return a mapping of column name -> SQLAlchemy Column object for `model`."""
    return {c.name: c for c in model.__table__.columns}  # type: ignore[attr-defined]


def _parse_csv_row_for_model(model, row: Dict[str, str]) -> Dict[str, Any]:
    """Build kwargs for model constructor/update from a CSV row.

    Only includes attributes that exist on the model and casts values
    according to the column SQLAlchemy type.
    """
    cols = _model_columns_map(model)
    out: Dict[str, Any] = {}
    for key, raw in row.items():
        if key == "code":
            # `code` is handled explicitly by caller
            continue
        col = cols.get(key)
        if col is None:
            # Ignore unknown CSV columns silently
            continue
        out[key] = _cast_for_column(col.type, raw)
    return out


def _values_differ(old: Any, new: Any) -> bool:
    """Return True if DB-stored value `old` differs from CSV-derived value `new`."""
    return old != new


# ---------- CSV loading ----------

async def _load_csv_map(csv_path: str) -> Tuple[Dict[str, Dict[str, str]], List[str], List[str], int]:
    """Load a CSV file into a mapping and collect metadata.

    Args:
        csv_path: Absolute path to the CSV.

    Returns:
        Tuple containing:
            - code_map: Dict[code, row dict]
            - headers: List[str] headers as parsed by DictReader
            - duplicate_codes: List[str] duplicate code values encountered (last wins)
            - missing_code_rows: int count of rows with missing/blank code
    """
    if not os.path.exists(csv_path):
        log.warning("CSV file not found: %s", csv_path)
        return {}, [], [], 0

    async with aiofiles.open(csv_path, mode="r", encoding="utf-8") as f:
        content = await f.read()

    lines = [ln for ln in content.splitlines() if ln.strip()]
    if not lines:
        return {}, [], [], 0

    reader = csv.DictReader(lines)
    headers = reader.fieldnames or []
    code_map: Dict[str, Dict[str, str]] = {}
    duplicate_codes: List[str] = []
    missing_code_rows = 0

    for row in reader:
        code = (row.get("code") or "").strip()
        if not code:
            missing_code_rows += 1
            continue
        if code in code_map:
            duplicate_codes.append(code)
        code_map[code] = row

    return code_map, headers, duplicate_codes, missing_code_rows


# ---------- core sync functions ----------

async def _sync_model_from_csv(model, csv_filename: str) -> None:
    """Upsert a simple code-based table from a CSV file.

    Behavior:
        - Inserts rows present in CSV but missing in DB.
        - Updates attributes if values differ (type-aware casting).
        - Clears `del_ts` for rows previously soft-deleted (restore).
        - Soft-deletes DB rows not present in CSV by setting `del_ts` to now.

    Args:
        model: SQLAlchemy mapped class (e.g., `Fuel` or `Language`).
        csv_filename: File name inside the CSV assets directory.
    """
    csv_path = os.path.join(ASSETS_CSV_DIR, csv_filename)
    csv_map, headers, duplicate_codes, missing_code_rows = await _load_csv_map(csv_path)

    # Warn about CSV issues
    if "code" not in headers:
        log.warning("[%s] Missing required 'code' column; nothing to do.", csv_filename)
        return
    if duplicate_codes:
        log.warning("[%s] Duplicate code values found (last occurrence wins): %s", csv_filename,
                    sorted(set(duplicate_codes)))
    if missing_code_rows:
        log.warning("[%s] Rows missing 'code': %d (skipped)", csv_filename, missing_code_rows)

    # Warn about unknown columns that won't be used
    model_cols = set(_model_columns_map(model).keys())
    unknown_cols = set([h for h in headers if h != "code"]) - model_cols
    if unknown_cols:
        log.warning("[%s] Unknown CSV columns ignored for %s: %s", csv_filename, model.__name__, sorted(unknown_cols))

    async with AsyncSession() as session:
        # Fetch all existing items
        result = await session.execute(select(model))
        db_items = result.scalars().all()
        db_map = {item.code: item for item in db_items}  # type: ignore[attr-defined]
        now = datetime.now(timezone.utc)

        inserts = updates = restores = soft_deletes = 0

        # 1) Insert or update from CSV
        for code, row in csv_map.items():
            if code not in db_map:
                kwargs = {"code": code}
                kwargs.update(_parse_csv_row_for_model(model, row))
                session.add(model(**kwargs))
                inserts += 1
                continue

            # Update existing object
            obj = db_map[code]

            # Restore if soft-deleted
            if getattr(obj, "del_ts", None) is not None:
                obj.del_ts = None
                restores += 1

            # Update fields if changed
            parsed = _parse_csv_row_for_model(model, row)
            changed = False
            for key, new_val in parsed.items():
                if not hasattr(obj, key):
                    continue
                old_val = getattr(obj, key)
                if _values_differ(old_val, new_val):
                    setattr(obj, key, new_val)
                    changed = True
            if changed:
                updates += 1

        # 2) Soft-delete DB entries missing from CSV
        for code, obj in db_map.items():
            if code not in csv_map and getattr(obj, "del_ts", None) is None:
                obj.del_ts = now
                soft_deletes += 1

        await session.commit()

    # Summary
    log.info(
        "[%s] Sync %s: csv_rows=%d, inserted=%d, restored=%d, updated=%d, soft_deleted=%d",
        csv_filename,
        model.__name__,
        len(csv_map),
        inserts,
        restores,
        updates,
        soft_deletes,
    )


async def sync_config_tables() -> None:
    """Synchronize domain config tables from CSV assets.

    Currently syncs:
        - `Fuel` from `fuels.csv`
        - `Language` from `languages.csv`
    """
    await _sync_model_from_csv(Fuel, "fuels.csv")
    await _sync_model_from_csv(Language, "languages.csv")
