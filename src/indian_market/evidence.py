"""The only shape a market number is allowed to have."""

from __future__ import annotations

from typing import Any

FRESHNESS = frozenset(
    {"live_snapshot", "previous_session", "delayed_vendor", "filing", "fixture", "unavailable"}
)


def evidence(
    *,
    symbol: str,
    exchange: str,
    field: str,
    value: Any,
    unit: str,
    session_date: str | None,
    as_of_ist: str | None,
    source: str,
    freshness: str,
    series: str | None = None,
    ok: bool = True,
    detail: str | None = None,
) -> dict[str, Any]:
    if freshness not in FRESHNESS:
        raise ValueError(f"unknown freshness: {freshness}")
    item: dict[str, Any] = {
        "ok": ok,
        "symbol": symbol,
        "exchange": exchange,
        "series": series,
        "field": field,
        "value": value,
        "unit": unit,
        "session_date": session_date,
        "as_of_ist": as_of_ist,
        "source": source,
        "freshness": freshness,
    }
    if detail:
        item["detail"] = detail
    if not ok:
        item["value"] = None
    return item


def missing(
    *,
    symbol: str,
    exchange: str,
    field: str,
    source: str,
    detail: str,
    series: str | None = None,
) -> dict[str, Any]:
    return evidence(
        symbol=symbol,
        exchange=exchange,
        series=series,
        field=field,
        value=None,
        unit="",
        session_date=None,
        as_of_ist=None,
        source=source,
        freshness="unavailable",
        ok=False,
        detail=detail,
    )
