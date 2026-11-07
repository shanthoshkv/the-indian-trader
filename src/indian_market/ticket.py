"""A manual ticket. Nothing in this module contacts a broker."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from indian_market.evidence import evidence, missing
from indian_market.journal import add_human_yes
from indian_market.plan import HORIZONS
from indian_market.records import done, source_ok

_PRODUCT = {
    "intraday_cash": "MIS",
    "delivery": "CNC",
    "futures": "NRML",
    "options": "NRML",
}


def build_ticket(pack: dict[str, Any]) -> dict[str, Any]:
    symbol = pack["symbol"]
    exchange = pack["exchange"]
    series = pack.get("series") or "EQ"
    source = pack.get("source") or "unspecified"
    session = pack.get("session_date")
    items: list[dict[str, Any]] = []
    common = dict(
        symbol=symbol,
        exchange=exchange,
        series=series,
        session_date=session,
        as_of_ist=pack.get("as_of_ist"),
        source=source,
        freshness="fixture" if str(source).startswith("fixture:") else "previous_session",
    )
    horizon = pack.get("horizon")
    product = pack.get("product") or (_PRODUCT.get(horizon) if horizon in HORIZONS else None)
    side = str(pack.get("side") or "").lower()
    if horizon not in HORIZONS or product != _PRODUCT[horizon] or side not in {"buy", "sell"}:
        items.append(missing(symbol=symbol, exchange=exchange, series=series, field="ticket", source=source, detail="Horizon, product, and side do not make a cash, futures, or options ticket. Products are MIS, CNC, and NRML."))
        return done(items, symbol=symbol, exchange=exchange, ticket_status="invalid")
    if not source_ok(source) or not pack.get("quantity") or pack.get("quantity") <= 0:
        items.append(missing(symbol=symbol, exchange=exchange, series=series, field="ticket", source=source, detail="A ticket needs a source and a positive quantity."))
        return done(items, symbol=symbol, exchange=exchange, ticket_status="invalid")
    if pack.get("gate") != "PASS":
        items.append(missing(symbol=symbol, exchange=exchange, series=series, field="ticket", source=source, detail="The risk gate has not passed. No ticket."))
        return done(items, symbol=symbol, exchange=exchange, ticket_status="blocked")

    order_type = str(pack.get("order_type") or "LIMIT").upper()
    price = pack.get("limit_price")
    if order_type == "LIMIT" and price is None:
        items.append(missing(symbol=symbol, exchange=exchange, series=series, field="ticket", source=source, detail="A limit ticket needs a limit price."))
        return done(items, symbol=symbol, exchange=exchange, ticket_status="invalid")
    validity = str(pack.get("validity") or "DAY").upper()
    price_text = "MKT" if order_type == "MARKET" else price
    text = f"{exchange} {symbol} {series}\n{product} {side.upper()} {int(pack['quantity'])} {order_type} {price_text} {validity}"
    human_yes = pack.get("human_yes") is True or str(pack.get("human_yes")).lower() == "yes"
    path = pack.get("journal_path")
    stored = False
    if not human_yes:
        status = "draft"
        detail = "Manual text only. A human yes has not been given, and nothing was sent to a broker."
    elif not path:
        status = "draft"
        detail = "Human yes was in the pack, but no journal path was given, so the yes was not stored. Nothing was sent to a broker."
    else:
        written = add_human_yes(Path(path), {**pack, "ticket": text, "symbol": symbol, "exchange": exchange})
        if not written.get("ok"):
            items.append(missing(symbol=symbol, exchange=exchange, series=series, field="human_yes_stored", source=source, detail=written.get("detail") or "The yes was not stored."))
            status = "draft"
            detail = written.get("detail") or "The yes was not stored."
        else:
            stored = True
            status = "ready"
            detail = "Manual ticket. The human yes is in the journal. Nothing was sent to a broker."
    items.append(evidence(field="ticket", value=text, unit="text", detail=detail, **common))
    items.append(evidence(field="ticket_status", value=status, unit="label", **common))
    items.append(evidence(field="human_yes_stored", value=stored, unit="label", **common))
    return done(items, symbol=symbol, exchange=exchange, series=series, ticket_status=status, human_yes_stored=stored)
