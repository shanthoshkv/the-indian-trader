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


def calendar_status(as_of: date | datetime | str) -> dict:
    """A date after the review horizon is not a confirmed session. Past dates in the file stay usable."""
    sheet = _calendar()
    day = _as_date(as_of)
    reviewed = date.fromisoformat(sheet["last_reviewed"])
    horizon = int(sheet.get("review_horizon_days") or 180)
    stale_after = reviewed + timedelta(days=horizon)
    return {
        "ok": day <= stale_after,
        "last_reviewed": sheet["last_reviewed"],
        "as_of": day.isoformat(),
        "review_horizon_days": horizon,
        "stale_after": stale_after.isoformat(),
    }


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
    if not calendar_status(day)["ok"]:
        return False
    if muhurat(day):
        return True
    if is_weekend(day):
        return False
    return holiday(day, exchange) is None


def previous_trading_day(day: date | datetime | str, exchange: str = "NSE") -> date:
    cursor = _as_date(day) - timedelta(days=1)
    for _ in range(400):
        if is_trading_day(cursor, exchange):
            return cursor
        cursor -= timedelta(days=1)
    raise ValueError("The holiday list does not confirm a previous session.")


def next_trading_day(day: date | datetime | str, exchange: str = "NSE") -> date:
    cursor = _as_date(day) + timedelta(days=1)
    for _ in range(400):
        if not calendar_status(cursor)["ok"]:
            break
        if is_trading_day(cursor, exchange):
            return cursor
        cursor += timedelta(days=1)
    raise ValueError("The holiday list is stale for that date. The next session was not confirmed.")


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
    status = calendar_status(day)
    if not status["ok"]:
        return _finish(
            {
                "phase": "closed",
                "date": day.isoformat(),
                "exchange": exchange.upper(),
                "name": None,
                "as_of_ist": now.isoformat(timespec="seconds"),
                "detail": "The holiday list is past its review date. This session was not confirmed.",
            },
            status,
        )
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
        return _finish(
            {
                "phase": phase,
                "date": day.isoformat(),
                "exchange": exchange.upper(),
                "name": special["name"],
                "as_of_ist": now.isoformat(timespec="seconds"),
            },
            status,
        )

    closed = holiday(day, exchange)
    if is_weekend(day) or closed:
        return _finish(
            {
                "phase": "holiday" if closed else "closed",
                "date": day.isoformat(),
                "exchange": exchange.upper(),
                "name": None if not closed else closed["name"],
                "as_of_ist": now.isoformat(timespec="seconds"),
            },
            status,
        )

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
    return _finish(
        {
            "phase": phase,
            "date": day.isoformat(),
            "exchange": exchange.upper(),
            "name": None,
            "as_of_ist": now.isoformat(timespec="seconds"),
        },
        status,
    )


def _finish(payload: dict, status: dict) -> dict:
    payload["calendar_ok"] = status["ok"]
    payload["calendar_stale_after"] = status["stale_after"]
    return payload
