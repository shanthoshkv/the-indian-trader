"""A trade plan from a surveillance result and a tape or levels result already on disk."""

from __future__ import annotations

from typing import Any

from indian_market.evidence import evidence, missing
from indian_market.records import done, source_ok

HORIZONS = ("intraday_cash", "delivery", "futures", "options")
_CONTEXT = {
    "prev_high",
    "prev_low",
    "prev_close",
    "vwap",
    "opening_range_high",
    "opening_range_low",
    "cpr_pivot",
    "cpr_top",
    "cpr_bottom",
    "week_high",
    "week_low",
    "close",
}


def read_plan(pack: dict[str, Any]) -> dict[str, Any]:
    symbol = pack["symbol"]
    exchange = pack["exchange"]
    series = pack.get("series")
    source = pack.get("source") or "unspecified"
    session = pack.get("session_date")
    as_of = pack.get("as_of_ist")
    items: list[dict[str, Any]] = []
    if not source_ok(source) or not session:
        items.append(missing(symbol=symbol, exchange=exchange, series=series, field="plan", source=source, detail="A plan needs a session date and a source."))
        return done(items, symbol=symbol, exchange=exchange, plan_status="incomplete")

    common = dict(symbol=symbol, exchange=exchange, series=series, session_date=session, as_of_ist=as_of, source=source, freshness="fixture" if source.startswith("fixture:") else "previous_session")
    status = _status(pack, items, common, source, symbol, exchange, series)
    horizon = pack.get("horizon")
    side = pack.get("side")
    if horizon not in HORIZONS or side not in {"long", "short"}:
        items.append(missing(symbol=symbol, exchange=exchange, series=series, field="horizon", source=source, detail="Horizon is intraday_cash, delivery, futures, or options. Side is long or short."))
        status = "incomplete"
    else:
        items.append(evidence(field="horizon", value=horizon, unit="label", **common))
        items.append(evidence(field="side", value=side, unit="label", **common))

    entry, stop, target = pack.get("entry"), pack.get("invalidation"), pack.get("target")
    if None in (entry, stop, target):
        items.append(missing(symbol=symbol, exchange=exchange, series=series, field="r_multiple", source=source, detail="Entry, invalidation, and target are all required."))
        status = "incomplete" if status == "ready" else status
    else:
        items.append(evidence(field="entry", value=entry, unit="INR", **common))
        items.append(evidence(field="invalidation", value=stop, unit="INR", **common))
        items.append(evidence(field="target", value=target, unit="INR", **common))
        if side not in {"long", "short"}:
            items.append(missing(symbol=symbol, exchange=exchange, series=series, field="r_multiple", source=source, detail="Side is long or short."))
        else:
            risk = (entry - stop) if side == "long" else (stop - entry)
            reward = (target - entry) if side == "long" else (entry - target)
            if risk <= 0 or reward <= 0:
                items.append(missing(symbol=symbol, exchange=exchange, series=series, field="r_multiple", source=source, detail="Invalidation or target is on the wrong side of entry."))
                if status == "ready":
                    status = "invalid"
            else:
                items.append(evidence(field="r_multiple", value=round(reward / risk, 4), unit="ratio", detail="Reward divided by the distance from entry to invalidation.", **common))

    if horizon in {"futures", "options"} and status == "ready":
        status = _contract(pack, items, common, source, symbol, exchange, series, horizon)

    items.append(evidence(field="plan_status", value=status, unit="label", detail="ready can be sized. blocked, invalid, and incomplete cannot.", **common))
    return done(items, symbol=symbol, exchange=exchange, series=series, plan_status=status)


def _status(pack, items, common, source, symbol, exchange, series) -> str:
    surveillance = pack.get("surveillance") or {}
    clearance = surveillance.get("clearance")
    if clearance not in {"clear", "caution", "blocked"} or not surveillance.get("source") or not surveillance.get("session_date"):
        items.append(missing(symbol=symbol, exchange=exchange, series=series, field="surveillance", source=source, detail="A surveillance result with clearance, source, and session date has to already be on disk."))
        context_ok = _context(pack)
        if not context_ok:
            items.append(missing(symbol=symbol, exchange=exchange, series=series, field="context", source=source, detail="A tape or levels result with at least one ok price field has to already be on disk."))
        return "incomplete"
    items.append(evidence(field="clearance", value=clearance, unit="label", detail=f"surveillance session {surveillance['session_date']}", **common))
    if not _context(pack):
        items.append(missing(symbol=symbol, exchange=exchange, series=series, field="context", source=source, detail="A tape or levels result with at least one ok price field has to already be on disk."))
        return "incomplete"
    horizon = pack.get("horizon")
    if clearance == "blocked" and horizon in {"futures", "options"}:
        return "blocked"
    if pack.get("trade_for_trade") and horizon == "intraday_cash":
        return "blocked"
    return "ready"


def _contract(pack, items, common, source, symbol, exchange, series, horizon) -> str:
    if not pack.get("expiry_date") or not pack.get("lot_size"):
        items.append(missing(symbol=symbol, exchange=exchange, series=series, field="contract", source=source, detail="Futures and options need an expiry date and a lot size from the contract file."))
        return "incomplete"
    items.append(evidence(field="expiry_date", value=pack["expiry_date"], unit="date", **common))
    items.append(evidence(field="lot_size", value=pack["lot_size"], unit="units", **common))
    if horizon == "options":
        kind = str(pack.get("option_type") or "").upper()
        if pack.get("strike") is None or kind not in {"CE", "PE"}:
            items.append(missing(symbol=symbol, exchange=exchange, series=series, field="option", source=source, detail="An option needs a strike and CE or PE."))
            return "incomplete"
        items.append(evidence(field="strike", value=pack["strike"], unit="INR", **common))
        items.append(evidence(field="option_type", value=kind, unit="label", **common))
    return "ready"


def _context(pack: dict) -> bool:
    for key in ("levels", "tape"):
        block = pack.get(key) or {}
        for item in block.get("items") or []:
            if item.get("ok") and item.get("field") in _CONTEXT and item.get("value") is not None:
                return True
    return False
