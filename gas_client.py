# -*- coding: utf-8 -*-
from __future__ import annotations

import datetime
from typing import Optional

from speedrun_api import (
    PlayerEntry,
    SpeedrunAPIError as GasClientError,
    fetch_leaderboard,
)


def fetch_division_data(division_key: str) -> tuple[list[PlayerEntry], str]:
    """speedrun.comから直接100件取得して返す"""
    entries = fetch_leaderboard(division_key, 100)
    return entries, datetime.datetime.now(datetime.timezone.utc).isoformat()


def refresh_division(division_key: Optional[str] = None) -> None:
    pass
