"""Open book against the mandate. A missing price stays blank. This does not resize or order."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from indian_market.evidence import evidence, missing
from indian_market.journal import read_events, reconstruct
from indian_market.records import done, freshness_for, source_ok
from indian_market.universe import resolve

_OPEN = {None, "open"}
_SHORT = {"short", "sell"}


def read_book(pack: dict[str, Any]) -> dict[str, Any]:
    source = pack.get("source") or "unspecified"
    session = pack.get("session_date")
    mandate = pack.get("mandate") or {}
    if not source_ok(source):
        item = missing(symbol="NSE", exchange="NSE", field="gross_inr", source=source, detail="The book needs a source.")
        return done([item])
    entries = _entries(pack)
    if entries is None:
        item = missing(symbol="NSE", exchange="NSE", field="gross_inr", source=source, detail="Pass journal rows or a journal path. Nothing was inferred.")
        return done([item])
    open_rows = [row for row in entries if row.get("outcome") in _OPEN]
    prices = {}
    for row in pack.get("prices") or []:
        symbol = str(row.get("symbol") or "").upper()
        if symbol:
            prices[symbol] = row
    items: list[dict[str, Any]] = []
    gross = 0.0
    net = 0.0
    priced = True
    sectors: dict[str, float] = {}
    for row in open_rows:
        leg = _one(row, prices, mandate, source, session, items, sectors)
        if leg is None:
            priced = False
            continue
        gross += abs(leg)
        net += leg
    fresh = freshness_for(source, "filing")
    if open_rows and priced:
        items.append(evidence(symbol="NSE", exchange="NSE", field="gross_inr", value=round(gross, 2), unit="INR", session_date=session, as_of_ist=None, source=source, freshness=fresh, detail="Sum of absolute quantity times the price file. Closed rows are excluded."))
        items.append(evidence(symbol="NSE", exchange="NSE", field="net_inr", value=round(net, 2), unit="INR", session_date=session, as_of_ist=None, source=source, freshness=fresh, detail="Long quantity is positive. Short quantity is negative."))
    elif not open_rows:
        items.append(evidence(symbol="NSE", exchange="NSE", field="gross_inr", value=0, unit="INR", session_date=session, as_of_ist=None, source=source, freshness=fresh, detail="No open journal row."))
        items.append(evidence(symbol="NSE", exchange="NSE", field="net_inr", value=0, unit="INR", session_date=session, as_of_ist=None, source=source, freshness=fresh, detail="No open journal row."))
    else:
        items.append(missing(symbol="NSE", exchange="NSE", field="gross_inr", source=source, detail="An open row has no price in the file. Gross was not filled."))
        items.append(missing(symbol="NSE", exchange="NSE", field="net_inr", source=source, detail="An open row has no price in the file. Net was not filled."))
    _caps(items, mandate, sectors, source, session, fresh)
    open_risk = round(sum(float(row.get("planned_risk_inr") or 0) for row in open_rows), 2)
    items.append(evidence(symbol="NSE", exchange="NSE", field="open_risk_inr", value=open_risk, unit="INR", session_date=session, as_of_ist=None, source=source, freshness=fresh, detail="Sum of planned risk on rows that are still open."))
    return done(items)


def _entries(pack: dict[str, Any]) -> list[dict[str, Any]] | None:
    if pack.get("entries") is not None:
        return list(pack["entries"])
    journal = pack.get("journal")
    if not journal:
        return None
    return reconstruct(read_events(Path(journal)))


def _signed(side: str | None, qty: float) -> float:
    if str(side or "long").lower() in _SHORT:
        return -abs(qty)
    return abs(qty)


def _one(row, prices, mandate, source, session, items, sectors) -> float | None:
    symbol = str(row.get("symbol") or "")
    exchange = row.get("exchange") or "NSE"
    resolved = resolve(symbol, exchange)
    if not resolved["ok"]:
        items.append(missing(symbol=symbol or "NSE", exchange=exchange, field="weight_pct", source=source, detail=resolved.get("detail") or "Outside NSE and BSE."))
        return None
    symbol = resolved["symbol"]
    exchange = resolved["exchange"]
    quote = prices.get(symbol)
    qty = row.get("qty")
    fresh = freshness_for(source, "filing")
    common = dict(symbol=symbol, exchange=exchange, series=resolved.get("series"), session_date=session, as_of_ist=None, source=source, freshness=fresh)
    if quote is None or quote.get("price") is None or qty is None:
        items.append(missing(symbol=symbol, exchange=exchange, series=resolved.get("series"), field="weight_pct", source=source, detail="Price or quantity is not in the files."))
        items.append(missing(symbol=symbol, exchange=exchange, series=resolved.get("series"), field="days_to_exit", source=source, detail="Price, quantity, or volume is not in the files."))
        return None
    signed = _signed(row.get("side"), float(qty))
    amount = abs(signed * float(quote["price"]))
    book = mandate.get("book_inr")
    if book:
        weight = round(amount / float(book) * 100, 4)
        items.append(evidence(field="weight_pct", value=weight, unit="percent", detail=symbol, **common))
        cap = mandate.get("single_name_cap_pct")
        if cap is not None and weight > float(cap):
            items.append(evidence(field="cap_breach", value=symbol, unit="label", detail=f"Weight {weight} is above the single-name cap {cap}. This command does not cut it.", **common))
    else:
        items.append(missing(symbol=symbol, exchange=exchange, series=resolved.get("series"), field="weight_pct", source=source, detail="The mandate has no book size. Weight was not filled."))
    participation = mandate.get("max_participation_pct")
    volume = quote.get("volume")
    if participation and volume:
        per_day = float(volume) * float(participation) / 100.0
        if per_day > 0:
            items.append(evidence(field="days_to_exit", value=round(abs(float(qty)) / per_day, 4), unit="days", detail="Quantity divided by the participation cap times the volume in the file.", **common))
        else:
            items.append(missing(symbol=symbol, exchange=exchange, series=resolved.get("series"), field="days_to_exit", source=source, detail="Volume or the participation cap is zero."))
    else:
        items.append(missing(symbol=symbol, exchange=exchange, series=resolved.get("series"), field="days_to_exit", source=source, detail="Volume or the participation cap was not supplied."))
    sector = quote.get("sector")
    if sector and book:
        sectors[str(sector)] = sectors.get(str(sector), 0.0) + amount
    return signed * float(quote["price"])


def _caps(items, mandate, sectors, source, session, fresh) -> None:
    cap = mandate.get("sector_cap_pct")
    book = mandate.get("book_inr")
    if not sectors or not book or cap is None:
        items.append(missing(symbol="NSE", exchange="NSE", field="sector_weight_pct", source=source, detail="Sector weights need a sector on the price file, a book size, and a sector cap."))
        return
    for sector, amount in sectors.items():
        weight = round(amount / float(book) * 100, 4)
        items.append(evidence(symbol="NSE", exchange="NSE", field="sector_weight_pct", value=weight, unit="percent", session_date=session, as_of_ist=None, source=source, freshness=fresh, detail=sector))
        if weight > float(cap):
            items.append(evidence(symbol="NSE", exchange="NSE", field="cap_breach", value=sector, unit="label", session_date=session, as_of_ist=None, source=source, freshness=fresh, detail=f"Sector weight {weight} is above the cap {cap}. This command does not cut it."))
