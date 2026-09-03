# -*- coding: utf-8 -*-
"""
リーダーボードのキャッシュ管理。
- world / jp: 独立してメモリおよびディスク（cache/*.json）に保存
- na / eu / as / oc / sa / af / other: worldキャッシュから動的に抽出
"""

from __future__ import annotations

import copy
import json
import logging
import os
import time
from dataclasses import asdict
from typing import Optional

import config
from gas_client import GasClientError, PlayerEntry, fetch_division_data, refresh_division

logger = logging.getLogger("cache_manager")

# メモリキャッシュ: key = f"{country}:{division}" -> {"entries": [...], "updated_at": float}
_memory_cache: dict[str, dict] = {}


def _cache_key(country: str, division: str) -> str:
    return f"{country}:{division}"


def _cache_file_path(key: str) -> str:
    safe_key = key.replace(":", "_")
    return os.path.join(config.CACHE_DIR, f"{safe_key}.json")


def _save_to_disk(key: str, entries: list[PlayerEntry], updated_at: float) -> None:
    try:
        os.makedirs(config.CACHE_DIR, exist_ok=True)
        payload = {
            "updated_at": updated_at,
            "entries": [asdict(e) for e in entries],
        }
        with open(_cache_file_path(key), "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False)
    except OSError as e:
        logger.warning("キャッシュのディスク保存に失敗しました (%s): %s", key, e)


def _load_from_disk(key: str) -> Optional[dict]:
    path = _cache_file_path(key)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        entries = [PlayerEntry(**e) for e in payload.get("entries", [])]
        return {"entries": entries, "updated_at": payload.get("updated_at", 0)}
    except (OSError, json.JSONDecodeError, TypeError) as e:
        logger.warning("キャッシュのディスク読み込みに失敗しました (%s): %s", key, e)
        return None


def _is_jp_player(entry: PlayerEntry) -> bool:
    if config.JP_WHITELIST and entry.player_name.strip().lower() in config.JP_WHITELIST:
        return True
    if entry.country_code:
        return entry.country_code.upper() == config.JP_COUNTRY_CODE.upper()
    return False


def _filter_jp(entries: list[PlayerEntry]) -> list[PlayerEntry]:
    filtered = [e for e in entries if _is_jp_player(e)]
    result = []
    for idx, e in enumerate(filtered, start=1):
        cloned = copy.copy(e)
        cloned.place = idx
        result.append(cloned)
    return result


def _filter_by_region(entries: list[PlayerEntry], region_key: str) -> list[PlayerEntry]:
    reg = region_key.lower()
    filtered = []

    if reg in config.REGION_COUNTRIES:
        allowed_countries = config.REGION_COUNTRIES[reg]
        for e in entries:
            code = (e.country_code or "").strip().lower()
            if reg == "as" and _is_jp_player(e):
                filtered.append(e)
            elif code and code in allowed_countries:
                filtered.append(e)

    elif reg == "other":
        all_assigned = set()
        for c_set in config.REGION_COUNTRIES.values():
            all_assigned.update(c_set)

        for e in entries:
            if _is_jp_player(e):
                continue
            code = (e.country_code or "").strip().lower()
            if not code or code not in all_assigned:
                filtered.append(e)

    sliced = filtered[: config.MAX_ROWS_REGION_DISPLAY]
    result = []
    for idx, e in enumerate(sliced, start=1):
        cloned = copy.copy(e)
        cloned.place = idx
        result.append(cloned)
    return result


def _iso_to_epoch(iso_str: Optional[str]) -> float:
    if not iso_str:
        return time.time()
    try:
        import datetime as _dt
        dt = _dt.datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.timestamp()
    except (ValueError, TypeError):
        return time.time()


async def refresh_all() -> None:
    for division_key in config.DIVISIONS.keys():
        try:
            raw_entries, updated_at_iso = fetch_division_data(division_key)
        except GasClientError as e:
            logger.error("データ取得に失敗しました (division=%s): %s", division_key, e)
            continue

        now = _iso_to_epoch(updated_at_iso)

        # 1. worldキャッシュ
        world_key = _cache_key("world", division_key)
        _memory_cache[world_key] = {"entries": raw_entries, "updated_at": now}
        _save_to_disk(world_key, raw_entries, now)

        # 2. jpキャッシュ（独立）
        jp_entries = _filter_jp(raw_entries)[: config.MAX_ROWS_JP_DISPLAY]
        jp_key = _cache_key("jp", division_key)
        _memory_cache[jp_key] = {"entries": jp_entries, "updated_at": now}
        _save_to_disk(jp_key, jp_entries, now)

        logger.info(
            "キャッシュ更新完了: division=%s (world取得件数=%d件, jpキャッシュ件数=%d件)",
            division_key,
            len(raw_entries),
            len(jp_entries),
        )


def trigger_gas_refresh(division_key: Optional[str] = None) -> None:
    refresh_division(division_key)


def get_cached(country: str, division: str) -> Optional[dict]:
    key = _cache_key(country, division)
    if key in _memory_cache:
        return _memory_cache[key]

    disk_cached = _load_from_disk(key)
    if disk_cached is not None:
        _memory_cache[key] = disk_cached
        return disk_cached

    return None


def get_page(country: str, division: str, page: int) -> Optional[dict]:
    country_lower = country.lower()

    if country_lower == "jp":
        cached = get_cached("jp", division)
        if cached is None:
            return None
        all_entries = cached["entries"]

    elif country_lower == "world":
        cached = get_cached("world", division)
        if cached is None:
            return None
        target = cached["entries"][: config.MAX_ROWS_WORLD_DISPLAY]
        all_entries = []
        for idx, e in enumerate(target, start=1):
            cloned = copy.copy(e)
            cloned.place = idx
            all_entries.append(cloned)

    else:
        cached = get_cached("world", division)
        if cached is None:
            return None
        all_entries = _filter_by_region(cached["entries"], country_lower)

    max_page = max(1, -(-len(all_entries) // config.ROWS_PER_PAGE))
    page = max(1, min(page, max_page))

    start = (page - 1) * config.ROWS_PER_PAGE
    end = start + config.ROWS_PER_PAGE
    page_entries = all_entries[start:end]

    return {
        "entries": page_entries,
        "updated_at": cached["updated_at"],
        "page": page,
        "max_page": max_page,
    }


def is_stale(updated_at: float) -> bool:
    return (time.time() - updated_at) > (config.CACHE_TTL_MINUTES * 60)
