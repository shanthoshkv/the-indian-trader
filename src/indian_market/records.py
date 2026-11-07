"""Shared checks for session and company packs."""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any

from indian_market.calendar_in import IST

_SOURCE = re.compile(r"^(https?://|NSE\b|BSE\b|fixture:)", re.IGNORECASE)


def source_ok(source: str | None) -> bool:
    return bool(source) and bool(_SOURCE.match(source.strip()))


def as_ist(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=IST)
    return parsed.astimezone(IST)


def as_date(value: str) -> date:
    return date.fromisoformat(value[:10])


def freshness_for(source: str, fallback: str) -> str:
    if source.startswith("fixture:"):
        return "fixture"
    return fallback


def done(items: list[dict[str, Any]], **extra: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {"ok": any(item["ok"] for item in items), "items": items}
    payload.update(extra)
    return payload
