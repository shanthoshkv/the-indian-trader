"""Previous-day range, weekly range, VWAP, central pivot, and opening range."""

from __future__ import annotations

from datetime import date
from typing import Any

from indian_market.evidence import evidence, missing
from indian_market.records import as_date, done, source_ok
from indian_market.tape import in_opening_range, typical_vwap


def read_levels(pack: dict[str, Any]) -> dict[str, Any]:
    symbol = pack["symbol"]
    exchange = pack["exchange"]
    series = pack.get("series")
    source = pack.get("source") or "unspecified"
    session = pack.get("session_date")
    as_of = pack.get("as_of_ist")
    freshness = "fixture" if source.startswith("fixture:") else (pack.get("freshness") or "previous_session")
    items: list[dict[str, Any]] = []
    if not source_ok(source):
        items.append(missing(symbol=symbol, exchange=exchange, series=series, field="levels", source=source, detail="Levels need a source."))
        return done(items, symbol=symbol, exchange=exchange, series=series)

    common = dict(symbol=symbol, exchange=exchange, series=series, session_date=session, as_of_ist=as_of, source=source, freshness=freshness)
    bars = sorted(pack.get("daily_bars") or [], key=lambda bar: bar["date"])
    previous = [bar for bar in bars if session is None or bar["date"] < session]
    if not previous:
        items.append(missing(symbol=symbol, exchange=exchange, series=series, field="prev_high", source=source, detail="No completed daily bar before the session date."))
    else:
        last = previous[-1]
        for field, key in (("prev_high", "high"), ("prev_low", "low"), ("prev_close", "close")):
            items.append(evidence(field=field, value=last[key], unit="INR", detail=f"daily bar {last['date']}", **common))
        _cpr(last, items, common)
        _week(previous, session, last["date"], items, common, source, symbol, exchange, series)

    _vwap(pack, items, common, source, symbol, exchange, series)
    _opening(pack, items, common, source, symbol, exchange, series)
    return done(items, symbol=symbol, exchange=exchange, series=series)


def _cpr(bar: dict, items: list, common: dict) -> None:
    high, low, close = bar["high"], bar["low"], bar["close"]
    pivot = (high + low + close) / 3.0
    bc = (high + low) / 2.0
    tc = (2.0 * pivot) - bc
    top = max(tc, bc)
    bottom = min(tc, bc)
    for field, value in (
        ("cpr_pivot", pivot),
        ("cpr_top", top),
        ("cpr_bottom", bottom),
    ):
        items.append(evidence(field=field, value=round(value, 4), unit="INR", detail="From the previous session high, low, and close.", **common))


def _week(previous: list, session: str | None, last_date: str, items: list, common: dict, source: str, symbol: str, exchange: str, series: str | None) -> None:
    anchor = as_date(session) if session else as_date(last_date)
    week = anchor.isocalendar()[:2]
    chosen = [bar for bar in previous if _same_week(bar["date"], week)]
    if not chosen:
        items.append(missing(symbol=symbol, exchange=exchange, series=series, field="week_high", source=source, detail="No daily bar in this ISO week."))
        return
    items.append(evidence(field="week_high", value=max(bar["high"] for bar in chosen), unit="INR", detail="Completed daily bars in the session's ISO week.", **common))
    items.append(evidence(field="week_low", value=min(bar["low"] for bar in chosen), unit="INR", detail="Completed daily bars in the session's ISO week.", **common))


def _same_week(iso: str, week: tuple[int, int]) -> bool:
    return date.fromisoformat(iso).isocalendar()[:2] == week


def _vwap(pack, items, common, source, symbol, exchange, series) -> None:
    if pack.get("vwap") is not None:
        items.append(evidence(field="vwap", value=pack["vwap"], unit="INR", detail="VWAP supplied on the pack.", **common))
        return
    bars = pack.get("bars_1m") or []
    if not bars:
        items.append(missing(symbol=symbol, exchange=exchange, series=series, field="vwap", source=source, detail="No VWAP and no minute bars."))
        return
    value = typical_vwap(bars)
    items.append(
        evidence(
            field="vwap",
            value=None if value is None else round(value, 4),
            unit="INR",
            detail="typical price (H+L+C)/3 times volume, on the bars supplied",
            **common,
        )
    )


def _opening(pack, items, common, source, symbol, exchange, series) -> None:
    if pack.get("opening_range_high") is not None and pack.get("opening_range_low") is not None:
        items.append(evidence(field="opening_range_high", value=pack["opening_range_high"], unit="INR", detail="Opening range supplied on the pack.", **common))
        items.append(evidence(field="opening_range_low", value=pack["opening_range_low"], unit="INR", detail="Opening range supplied on the pack.", **common))
        return
    bars = [bar for bar in (pack.get("bars_1m") or []) if in_opening_range(bar["t"])]
    if not bars:
        items.append(missing(symbol=symbol, exchange=exchange, series=series, field="opening_range", source=source, detail="No opening-range bars for 09:15 inclusive to 09:30 exclusive IST."))
        return
    items.append(evidence(field="opening_range_high", value=max(bar["h"] for bar in bars), unit="INR", detail="09:15 inclusive to 09:30 exclusive IST", **common))
    items.append(evidence(field="opening_range_low", value=min(bar["l"] for bar in bars), unit="INR", detail="09:15 inclusive to 09:30 exclusive IST", **common))
