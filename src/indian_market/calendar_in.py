"""NSE and BSE session clock. IST has no daylight saving."""

from __future__ import annotations

import json
from datetime import date, datetime, time, timedelta, timezone
from functools import lru_cache

from indian_market.paths import data_dir

IST = timezone(timedelta(hours=5, minutes=30))


@lru_cache(maxsize=1)
def _calendar() -> dict:
    return json.loads((data_dir() / "holidays.json").read_text(encoding="utf-8"))


def _as_date(value: date | datetime | str) -> date:
    if isinstance(value, datetime):
        return value.astimezone(IST).date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(value)


def holiday(day: date | datetime | str, exchange: str = "NSE") -> dict | None:
    iso = _as_date(day).isoformat()
    exchange = exchange.upper()
    for row in _calendar()["closed"]:
        if row["date"] == iso and exchange in row["exchanges"]:
            return row
    return None


def muhurat(day: date | datetime | str) -> dict | None:
    iso = _as_date(day).isoformat()
    for row in _calendar()["muhurat"]:
        if row["date"] == iso:
            return row
    return None


def is_weekend(day: date) -> bool:
    return day.weekday() >= 5


def is_trading_day(day: date | datetime | str, exchange: str = "NSE") -> bool:
    day = _as_date(day)
    if muhurat(day):
        return True
    if is_weekend(day):
        return False
    return holiday(day, exchange) is None


def previous_trading_day(day: date | datetime | str, exchange: str = "NSE") -> date:
    cursor = _as_date(day) - timedelta(days=1)
    while not is_trading_day(cursor, exchange):
        cursor -= timedelta(days=1)
    return cursor


def _clock(now: datetime) -> time:
    return now.astimezone(IST).time().replace(microsecond=0)


def _at(hhmm: str) -> time:
    hour, minute = hhmm.split(":")
    return time(int(hour), int(minute))


def session_state(now: datetime | None = None, exchange: str = "NSE") -> dict:
    if now is None:
        now = datetime.now(IST)
    elif now.tzinfo is None:
        now = now.replace(tzinfo=IST)
    else:
        now = now.astimezone(IST)
    day = now.date()
    special = muhurat(day)
    if special:
        clock = _clock(now)
        start = _at(special["preopen_start"])
        cont = _at(special["continuous_start"])
        end = _at(special["continuous_end"])
        if start <= clock < cont:
            phase = "preopen"
        elif cont <= clock <= end:
            phase = "muhurat"
        else:
            phase = "closed"
        return {
            "phase": phase,
            "date": day.isoformat(),
            "exchange": exchange.upper(),
            "name": special["name"],
            "as_of_ist": now.isoformat(timespec="seconds"),
        }

    closed = holiday(day, exchange)
    if is_weekend(day) or closed:
        return {
            "phase": "holiday" if closed else "closed",
            "date": day.isoformat(),
            "exchange": exchange.upper(),
            "name": None if not closed else closed["name"],
            "as_of_ist": now.isoformat(timespec="seconds"),
        }

    clock = _clock(now)
    if clock < _at("09:00"):
        phase = "closed"
    elif clock < _at("09:05"):
        phase = "preopen_market"
    elif clock < _at("09:10"):
        phase = "preopen_limit"
    elif clock < _at("09:12"):
        phase = "preopen_match"
    elif clock < _at("09:15"):
        phase = "preopen_buffer"
    elif clock <= _at("15:30"):
        phase = "continuous"
    else:
        phase = "closed"
    return {
        "phase": phase,
        "date": day.isoformat(),
        "exchange": exchange.upper(),
        "name": None,
        "as_of_ist": now.isoformat(timespec="seconds"),
    }
