"""Listed expiry, put-call ratio, and open interest near spot.

Lot size and freeze quantity are copied from the contract file. They are
never filled from memory. This module does not recommend a strategy.
"""

from __future__ import annotations

from typing import Any

from indian_market.evidence import evidence, missing
from indian_market.records import as_date, done, source_ok

_BAND = 0.01


def read_options(pack: dict[str, Any]) -> dict[str, Any]:
    symbol = pack["symbol"]
    exchange = pack["exchange"]
    series = pack.get("series")
    source = pack.get("source") or "unspecified"
    session = pack.get("session_date")
    as_of = pack.get("as_of_ist")
    freshness = "previous_session"
    items: list[dict[str, Any]] = []
    if not session or not source_ok(source):
        items.append(missing(symbol=symbol, exchange=exchange, series=series, field="options", source=source, detail="The option file needs a session date and a source."))
        return done(items, symbol=symbol, exchange=exchange, series=series)

    common = dict(
        symbol=symbol,
        exchange=exchange,
        series=series,
        session_date=session,
        as_of_ist=as_of,
        source=source,
        freshness="fixture" if source.startswith("fixture:") else freshness,
    )
    expiry = pack.get("expiry")
    if not expiry:
        items.append(missing(symbol=symbol, exchange=exchange, series=series, field="nearest_expiry", source=source, detail="The contract file did not include the listed expiry."))
    elif as_date(expiry) < as_date(session):
        items.append(missing(symbol=symbol, exchange=exchange, series=series, field="nearest_expiry", source=source, detail="The listed expiry is before the session date."))
    else:
        items.append(evidence(field="nearest_expiry", value=expiry, unit="date", **common))
        items.append(evidence(field="days_to_expiry", value=(as_date(expiry) - as_date(session)).days, unit="days", **common))

    strikes = pack.get("strikes") or []
    call_oi = sum(row.get("call_oi") or 0 for row in strikes)
    put_oi = sum(row.get("put_oi") or 0 for row in strikes)
    if call_oi:
        items.append(evidence(field="put_call_ratio", value=round(put_oi / call_oi, 4), unit="ratio", detail="sum of put OI / sum of call OI on the strikes supplied", **common))
    else:
        items.append(missing(symbol=symbol, exchange=exchange, series=series, field="put_call_ratio", source=source, detail="Call open interest was zero or missing."))

    _around_spot(pack, strikes, items, common, source, symbol, exchange, series)

    vix = pack.get("india_vix_close")
    vix_session = pack.get("india_vix_session")
    if vix is None or not vix_session:
        items.append(missing(symbol="INDIAVIX", exchange="NSE", series="INDEX", field="india_vix_close", source=source, detail="India VIX previous close was not in the pack."))
    else:
        items.append(
            evidence(
                symbol="INDIAVIX",
                exchange="NSE",
                series="INDEX",
                field="india_vix_close",
                value=vix,
                unit="index",
                session_date=vix_session,
                as_of_ist=as_of,
                source=source,
                freshness="previous_session" if not source.startswith("fixture:") else "fixture",
            )
        )

    for field, key, detail in (
        ("lot_size", "lot_size", "Copied from the contract file. Not a hardcoded lot."),
        ("freeze_qty", "freeze_qty", "Copied from the contract file."),
    ):
        if pack.get(key) is None:
            items.append(missing(symbol=symbol, exchange=exchange, series=series, field=field, source=source, detail="Not in the contract file. Do not hardcode it."))
        else:
            items.append(evidence(field=field, value=pack[key], unit="units", detail=detail, **common))

    return done(items, symbol=symbol, exchange=exchange, series=series)


def _around_spot(pack, strikes, items, common, source, symbol, exchange, series) -> None:
    spot = pack.get("spot")
    if spot in (None, 0) or not strikes:
        items.append(missing(symbol=symbol, exchange=exchange, series=series, field="oi_around_spot", source=source, detail="Spot and at least one strike are required."))
        return
    near = [row for row in strikes if abs(row["strike"] - spot) / spot <= _BAND]
    if not near:
        near = [min(strikes, key=lambda row: abs(row["strike"] - spot))]
    names = ",".join(str(row["strike"]) for row in sorted(near, key=lambda row: row["strike"]))
    call_change = sum(row.get("call_oi_change") or 0 for row in near)
    put_change = sum(row.get("put_oi_change") or 0 for row in near)
    detail = f"strikes {names}; within 1 percent of spot, or the nearest strike"
    items.append(evidence(field="call_oi_change_around_spot", value=call_change, unit="contracts", detail=detail, **common))
    items.append(evidence(field="put_oi_change_around_spot", value=put_change, unit="contracts", detail=detail, **common))
