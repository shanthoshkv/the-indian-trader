"""Previous-session brief. Pre-open is included only after 09:00 IST."""

from __future__ import annotations

from datetime import time
from typing import Any

from indian_market.calendar_in import is_trading_day
from indian_market.evidence import evidence, missing
from indian_market.expiry import next_expiry
from indian_market.records import as_ist, done, freshness_for, source_ok
from indian_market.universe import resolve

_OPEN = time(9, 0)


def _blank(symbol: str, exchange: str, field: str, source: str, detail: str, series: str | None = None) -> dict[str, Any]:
    return missing(symbol=symbol, exchange=exchange, series=series, field=field, source=source, detail=detail)


def build_premarket(pack: dict[str, Any]) -> dict[str, Any]:
    source = pack.get("source") or "unspecified"
    session_date = pack.get("session_date")
    as_of = pack.get("as_of_ist")
    items: list[dict[str, Any]] = []

    for row in pack.get("closes") or []:
        resolved = resolve(row.get("symbol", ""), row.get("exchange"))
        if not resolved["ok"]:
            items.append(
                _blank(row.get("symbol") or "", row.get("exchange") or "", "previous_close", source, resolved["detail"])
            )
            continue
        if row.get("value") is None or not row.get("session_date"):
            items.append(
                _blank(resolved["symbol"], resolved["exchange"], "previous_close", source, "Previous close needs a value and a session date.", resolved.get("series"))
            )
            continue
        items.append(
            evidence(
                symbol=resolved["symbol"],
                exchange=resolved["exchange"],
                series=resolved.get("series"),
                field="previous_close",
                value=row["value"],
                unit="INR",
                session_date=row["session_date"],
                as_of_ist=as_of,
                source=source,
                freshness="previous_session",
            )
        )

    _preopen(pack, items, source, session_date, as_of)
    _flows(pack, items, source, as_of)
    _vix(pack, items, source, as_of)
    _announcements(pack, items, as_of)
    _gift(pack, items, as_of)
    _expiries(items, session_date, as_of, source)
    return done(items, session_date=session_date, as_of_ist=as_of)


def _preopen(pack: dict, items: list, source: str, session_date: str | None, as_of: str | None) -> None:
    row = pack.get("preopen") or {}
    symbol = (row.get("symbol") or "NIFTY")
    exchange = row.get("exchange") or "NSE"
    resolved = resolve(symbol, exchange)
    if not resolved["ok"]:
        items.append(_blank(symbol, exchange, "preopen", source, resolved["detail"]))
        return
    symbol = resolved["symbol"]
    exchange = resolved["exchange"]
    series = resolved.get("series")
    if not session_date or not is_trading_day(session_date, exchange):
        items.append(_blank(symbol, exchange, "preopen", source, "The cash session is not open on this date.", series))
        return
    if not as_of:
        items.append(_blank(symbol, exchange, "preopen", source, "Pre-open needs the brief time in IST.", series))
        return
    stamp = as_ist(as_of)
    if stamp.date().isoformat() != session_date or stamp.time() < _OPEN:
        items.append(
            _blank(symbol, exchange, "preopen", source, "Pre-open starts at 09:00 IST. No print is included before that.", series)
        )
        return
    if row.get("value") is None:
        items.append(_blank(symbol, exchange, "preopen", source, "No pre-open print was in the pack.", series))
        return
    printed = row.get("as_of_ist")
    if not printed or as_ist(printed).time() < _OPEN or as_ist(printed).date().isoformat() != session_date:
        items.append(
            _blank(symbol, exchange, "preopen", source, "The pre-open print is not timestamped at or after 09:00 IST on the session date.", series)
        )
        return
    items.append(
        evidence(
            symbol=symbol,
            exchange=exchange,
            series=series,
            field="preopen",
            value=row["value"],
            unit="INR",
            session_date=session_date,
            as_of_ist=printed,
            source=row.get("source") or source,
            freshness=freshness_for(row.get("source") or source, "live_snapshot"),
            detail="Indicative pre-open print. Not the official close.",
        )
    )


def _flows(pack: dict, items: list, source: str, as_of: str | None) -> None:
    session = pack.get("flows_session_date")
    for field, key in (("fii_cash_net", "fii_cash_crore"), ("dii_cash_net", "dii_cash_crore")):
        value = pack.get(key)
        if value is None or not session:
            items.append(
                _blank("FII" if field.startswith("fii") else "DII", "NSE", field, source, "FII and DII cash need a value and the session date they belong to.", "CASH")
            )
            continue
        items.append(
            evidence(
                symbol="FII" if field.startswith("fii") else "DII",
                exchange="NSE",
                series="CASH",
                field=field,
                value=value,
                unit="INR_crore",
                session_date=session,
                as_of_ist=as_of,
                source=source,
                freshness="previous_session",
                detail="Cash provisional or final figure for the named session. Not an intraday print.",
            )
        )


def _vix(pack: dict, items: list, source: str, as_of: str | None) -> None:
    row = pack.get("india_vix") or {}
    if row.get("close") is None or not row.get("session_date"):
        items.append(_blank("INDIAVIX", "NSE", "india_vix_close", source, "India VIX previous close was not in the pack.", "INDEX"))
        return
    items.append(
        evidence(
            symbol="INDIAVIX",
            exchange="NSE",
            series="INDEX",
            field="india_vix_close",
            value=row["close"],
            unit="index",
            session_date=row["session_date"],
            as_of_ist=as_of,
            source=source,
            freshness="previous_session",
        )
    )


def _announcements(pack: dict, items: list, as_of: str | None) -> None:
    rows = pack.get("announcements") or []
    if not rows:
        items.append(_blank("NSE", "NSE", "overnight_announcement", pack.get("source") or "unspecified", "No overnight announcement was in the pack."))
        return
    for row in rows:
        row_source = row.get("source") or ""
        resolved = resolve(row.get("symbol", ""), row.get("exchange"))
        if not resolved["ok"]:
            items.append(_blank(row.get("symbol") or "", row.get("exchange") or "NSE", "overnight_announcement", row_source or "unspecified", resolved["detail"]))
            continue
        if not row.get("headline") or not source_ok(row_source):
            items.append(
                _blank(resolved["symbol"], resolved["exchange"], "overnight_announcement", row_source or "unspecified", "An announcement needs a headline and an NSE, BSE, http, or fixture source.", resolved.get("series"))
            )
            continue
        items.append(
            evidence(
                symbol=resolved["symbol"],
                exchange=resolved["exchange"],
                series=resolved.get("series"),
                field="overnight_announcement",
                value=row["headline"],
                unit="text",
                session_date=row.get("session_date"),
                as_of_ist=as_of,
                source=row_source,
                freshness=freshness_for(row_source, "filing"),
            )
        )


def _gift(pack: dict, items: list, as_of: str | None) -> None:
    row = pack.get("gift_nifty")
    source = (row or {}).get("source") or pack.get("source") or "unspecified"
    if not row:
        items.append(
            _blank("GIFTNIFTY", "GIFT", "gift_nifty", source, "No GIFT Nifty print was supplied. Do not treat a memory of it as NSE cash.", "OFFSHORE")
        )
        return
    if (row.get("exchange") or "GIFT").upper() in {"NSE", "BSE"}:
        items.append(
            _blank("GIFTNIFTY", "GIFT", "gift_nifty", source, "GIFT Nifty is not an NSE or BSE cash print.", "OFFSHORE")
        )
        return
    if row.get("value") is None or not source_ok(row.get("source")):
        items.append(_blank("GIFTNIFTY", "GIFT", "gift_nifty", source, "GIFT Nifty needs a value and its own source.", "OFFSHORE"))
        return
    items.append(
        evidence(
            symbol="GIFTNIFTY",
            exchange="GIFT",
            series="OFFSHORE",
            field="gift_nifty",
            value=row["value"],
            unit="INR",
            session_date=None,
            as_of_ist=row.get("as_of_ist") or as_of,
            source=row["source"],
            freshness=freshness_for(row["source"], "delayed_vendor"),
            detail="Not an NSE or BSE cash print.",
        )
    )


def _expiries(items: list, session_date: str | None, as_of: str | None, source: str) -> None:
    if not session_date:
        for symbol, exchange in (("NIFTY", "NSE"), ("SENSEX", "BSE")):
            items.append(_blank(symbol, exchange, "weekly_expiry", source, "The brief has no session date, so expiry was not looked up.", "INDEX"))
        return
    for symbol, exchange in (("NIFTY", "NSE"), ("SENSEX", "BSE")):
        found = next_expiry(symbol, session_date)
        weekly = found.get("weekly") if found.get("ok") else None
        if not weekly:
            items.append(_blank(symbol, exchange, "weekly_expiry", exchange, "No weekly expiry was returned.", "INDEX"))
            continue
        items.append(
            evidence(
                symbol=symbol,
                exchange=exchange,
                series="INDEX",
                field="weekly_expiry",
                value=weekly,
                unit="date",
                session_date=session_date,
                as_of_ist=as_of,
                source=exchange,
                freshness="filing",
                detail="Holiday-shifted weekly date from this pack's calendar.",
            )
        )
