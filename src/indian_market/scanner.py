"""Opening-range breaks and high delivery inside a named list.

Banned names and trade-for-trade names are left out unless the pack sets
include_restricted. The scan does not look outside the list.
"""

from __future__ import annotations

from typing import Any

from indian_market.evidence import evidence, missing
from indian_market.records import done, source_ok
from indian_market.universe import resolve


def scan_list(pack: dict[str, Any]) -> dict[str, Any]:
    source = pack.get("source") or "unspecified"
    session = pack.get("session_date")
    as_of = pack.get("as_of_ist")
    names = pack.get("names") or []
    minimum = pack.get("min_delivery_pct")
    items: list[dict[str, Any]] = []
    if not names or not session or not source_ok(source) or minimum is None:
        items.append(missing(symbol="NSE", exchange="NSE", field="scan", source=source, detail="A scan needs a named list, a session date, a source, and a delivery threshold."))
        return done(items, session_date=session)
    allow = bool(pack.get("include_restricted"))
    for row in names:
        resolved = resolve(row.get("symbol", ""), row.get("exchange"))
        if not resolved["ok"]:
            items.append(missing(symbol=row.get("symbol") or "", exchange=row.get("exchange") or "NSE", field="scan_hit", source=source, detail=resolved["detail"]))
            continue
        reason = _restricted(row, resolved.get("series"))
        if reason and not allow:
            items.append(
                evidence(
                    symbol=resolved["symbol"],
                    exchange=resolved["exchange"],
                    series=resolved.get("series"),
                    field="scan_excluded",
                    value=reason,
                    unit="label",
                    session_date=session,
                    as_of_ist=as_of,
                    source=source,
                    freshness="fixture" if source.startswith("fixture:") else "previous_session",
                    detail="Excluded by default.",
                )
            )
            continue
        _hits(row, resolved, items, source, session, as_of, minimum, reason if allow else None)
    return done(items, session_date=session)


def _restricted(row: dict, series: str | None) -> str | None:
    if row.get("fo_ban"):
        return "fo_ban"
    if row.get("trade_for_trade") or str(row.get("series") or series or "").upper() == "BE":
        return "trade_for_trade"
    return None


def _hits(row, resolved, items, source, session, as_of, minimum, forced: str | None) -> None:
    common = dict(
        symbol=resolved["symbol"],
        exchange=resolved["exchange"],
        series=resolved.get("series"),
        session_date=session,
        as_of_ist=as_of,
        source=source,
        freshness="fixture" if source.startswith("fixture:") else "previous_session",
    )
    last = row.get("last")
    high, low = row.get("opening_range_high"), row.get("opening_range_low")
    if last is not None and high is not None and last > high:
        items.append(evidence(field="scan_hit", value="opening_range_break_up", unit="label", detail=forced or "last above the opening-range high", **common))
    elif last is not None and low is not None and last < low:
        items.append(evidence(field="scan_hit", value="opening_range_break_down", unit="label", detail=forced or "last below the opening-range low", **common))
    delivery = row.get("delivery_pct")
    if delivery is None:
        items.append(missing(**{k: common[k] for k in ("symbol", "exchange", "series")}, field="high_delivery", source=source, detail="Delivery percent was not in the row."))
    elif delivery >= minimum:
        items.append(evidence(field="scan_hit", value="high_delivery", unit="label", detail=f"delivery_pct={delivery}; threshold={minimum}", **common))
