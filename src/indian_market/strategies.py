"""Named setups. Each one builds a trade-plan pack from fields already on disk.

A failed trigger is an invalid plan. It is not a buy or a sell verdict.
"""

from __future__ import annotations

from typing import Any

from indian_market.calendar_in import muhurat, next_trading_day
from indian_market.evidence import evidence, missing
from indian_market.plan import read_plan
from indian_market.records import done, source_ok


def opening_range_break(pack: dict[str, Any]) -> dict[str, Any]:
    last, high, low = pack.get("last"), pack.get("opening_range_high"), pack.get("opening_range_low")
    if None in (last, high, low):
        return _stop(pack, "opening_range_break", "Last, opening-range high, and opening-range low are required.")
    if str(pack.get("series") or "").upper() == "BE":
        pack = {**pack, "trade_for_trade": True}
    if last > high:
        return _finish(_prices(pack, "opening_range_break", "intraday_cash", "long", last, low, None), {"opening_range_high": high, "opening_range_low": low})
    if last < low:
        return _finish(_prices(pack, "opening_range_break", "intraday_cash", "short", last, high, None), {"opening_range_high": high, "opening_range_low": low})
    return _stop(pack, "opening_range_break", "Last is inside the opening range.")


def previous_day_break(pack: dict[str, Any]) -> dict[str, Any]:
    last, high, low = pack.get("last"), pack.get("prev_high"), pack.get("prev_low")
    if None in (last, high, low):
        return _stop(pack, "previous_day_break", "Last, previous-day high, and previous-day low are required.")
    if last > high:
        return _finish(_prices(pack, "previous_day_break", "intraday_cash", "long", last, high, None), {"prev_high": high, "prev_low": low})
    if last < low:
        return _finish(_prices(pack, "previous_day_break", "intraday_cash", "short", last, low, None), {"prev_high": high, "prev_low": low})
    return _stop(pack, "previous_day_break", "Last is inside the previous day.")


def vwap_hold(pack: dict[str, Any]) -> dict[str, Any]:
    last, vwap, low = pack.get("last"), pack.get("vwap"), pack.get("opening_range_low")
    if None in (last, vwap, low):
        return _stop(pack, "vwap_hold", "Last, VWAP, and the opening-range low are required.")
    if last > vwap and last >= low:
        return _finish(_prices(pack, "vwap_hold", "intraday_cash", "long", last, vwap, None), {"vwap": vwap, "opening_range_low": low})
    return _stop(pack, "vwap_hold", "Price is not above VWAP with the opening-range low held.")


def delivery_rs(pack: dict[str, Any]) -> dict[str, Any]:
    delivery, rs = pack.get("delivery_pct"), pack.get("rs")
    floor, min_rs = pack.get("min_delivery_pct"), pack.get("min_rs")
    last, low = pack.get("last"), pack.get("prev_low")
    if None in (delivery, rs, floor, min_rs, last, low):
        return _stop(pack, "delivery_rs", "Delivery, relative strength, both thresholds, last, and previous low are required. Do not invent a threshold.")
    if delivery >= floor and rs > min_rs:
        built = _prices(pack, "delivery_rs", "delivery", "long", last, low, None)
        return _finish(built, {"prev_low": low, "close": last})
    return _stop(pack, "delivery_rs", "Delivery or relative strength is below the threshold in the pack.")


def sector_leader(pack: dict[str, Any]) -> dict[str, Any]:
    leader, sector = pack.get("leader"), pack.get("sector")
    if not leader or not sector:
        return _stop(pack, "sector_leader", "The leading sector and this name's sector are required.")
    if leader != sector:
        return _stop(pack, "sector_leader", f"{sector} is not the leading sector {leader}.")
    return _sector_plan(pack)


def post_result(pack: dict[str, Any]) -> dict[str, Any]:
    results, session = pack.get("results_date"), pack.get("session_date")
    last, prev = pack.get("last"), pack.get("prev_close")
    minimum = pack.get("min_gap_pct")
    if not results or not session or None in (last, prev) or minimum is None or not prev:
        return _stop(pack, "post_result", "Results date, session, previous close, last, and a minimum gap percent are required.")
    if session == results:
        return _stop(pack, "post_result", "The results session itself stays blocked.", status="blocked")
    nxt = next_trading_day(results, pack.get("exchange") or "NSE").isoformat()
    if session != nxt:
        return _stop(pack, "post_result", f"The next session after results is {nxt}.")
    gap = (last - prev) / prev * 100
    if abs(gap) < minimum:
        return _stop(pack, "post_result", "The gap is inside the minimum in the pack.")
    side = "long" if gap > 0 else "short"
    built = _prices(pack, "post_result", "intraday_cash", side, last, prev, None)
    result = _finish(built, {"prev_close": prev, "close": last})
    result["items"].extend(_event_notes(pack))
    if muhurat(session):
        result["muhurat"] = True
        result["items"].append(_note(pack, "muhurat", True, "This next session is Muhurat."))
    return result


SETUPS = {
    "orb": opening_range_break,
    "pdh": previous_day_break,
    "vwap": vwap_hold,
    "delivery": delivery_rs,
    "sector": sector_leader,
    "post": post_result,
}


def _sector_plan(pack: dict[str, Any]) -> dict[str, Any]:
    delivery, rs = pack.get("delivery_pct"), pack.get("rs")
    floor, min_rs = pack.get("min_delivery_pct"), pack.get("min_rs")
    last, low = pack.get("last"), pack.get("prev_low")
    if None in (delivery, rs, floor, min_rs, last, low):
        return _stop(pack, "sector_leader", "Delivery, relative strength, both thresholds, last, and previous low are required.")
    if delivery < floor or rs <= min_rs:
        return _stop(pack, "sector_leader", "The leader's name is below the delivery or relative-strength threshold.")
    return _finish(_prices(pack, "sector_leader", "delivery", "long", last, low, None), {"prev_low": low, "close": last})


def _prices(pack, setup, horizon, side, entry, stop, target) -> dict[str, Any]:
    risk = abs(entry - stop)
    if target is None:
        target = entry + 2 * risk if side == "long" else entry - 2 * risk
    surveillance = pack.get("surveillance") or {}
    return {
        "symbol": pack.get("symbol"),
        "exchange": pack.get("exchange"),
        "series": pack.get("series"),
        "session_date": pack.get("session_date"),
        "as_of_ist": pack.get("as_of_ist"),
        "source": pack.get("source"),
        "horizon": horizon,
        "side": side,
        "entry": entry,
        "invalidation": stop,
        "target": target,
        "setup": setup,
        "trade_for_trade": pack.get("trade_for_trade"),
        "expiry_date": pack.get("expiry_date"),
        "lot_size": pack.get("lot_size"),
        "strike": pack.get("strike"),
        "option_type": pack.get("option_type"),
        "surveillance": surveillance,
    }


def _finish(built: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    built = dict(built)
    built["levels"] = {"items": [{"ok": True, "field": key, "value": value} for key, value in context.items() if value is not None]}
    result = read_plan(built)
    result["setup"] = built["setup"]
    result["items"].insert(0, _note(built, "setup", built["setup"], "Setup card. The plan fields below are from trade-plan."))
    return result


def _stop(pack: dict[str, Any], setup: str, detail: str, status: str = "invalid") -> dict[str, Any]:
    symbol = pack.get("symbol") or "NSE"
    exchange = pack.get("exchange") or "NSE"
    source = pack.get("source") or "unspecified"
    items = [
        missing(symbol=symbol, exchange=exchange, series=pack.get("series"), field="trigger", source=source, detail=detail),
    ]
    if source_ok(source) and pack.get("session_date"):
        items.append(
            evidence(
                symbol=symbol,
                exchange=exchange,
                series=pack.get("series"),
                field="plan_status",
                value=status,
                unit="label",
                session_date=pack.get("session_date"),
                as_of_ist=pack.get("as_of_ist"),
                source=source,
                freshness="fixture" if str(source).startswith("fixture:") else "previous_session",
                detail=setup,
            )
        )
    return done(items, symbol=symbol, exchange=exchange, series=pack.get("series"), plan_status=status, setup=setup)


def _event_notes(pack: dict[str, Any]) -> list[dict[str, Any]]:
    notes = []
    if pack.get("concall"):
        notes.append(_note(pack, "concall", pack["concall"], "Quoted from the pack. Not a verdict."))
    else:
        notes.append(missing(symbol=pack.get("symbol") or "", exchange=pack.get("exchange") or "NSE", series=pack.get("series"), field="concall", source=pack.get("source") or "unspecified", detail="No concall line was in the pack."))
    if pack.get("ex_date"):
        notes.append(_note(pack, "ex_date", pack["ex_date"], "From the pack."))
    else:
        notes.append(missing(symbol=pack.get("symbol") or "", exchange=pack.get("exchange") or "NSE", series=pack.get("series"), field="ex_date", source=pack.get("source") or "unspecified", detail="No ex-date was in the pack."))
    return notes


def _note(pack: dict[str, Any], field: str, value: Any, detail: str) -> dict[str, Any]:
    source = pack.get("source") or "unspecified"
    return evidence(
        symbol=pack.get("symbol") or "NSE",
        exchange=pack.get("exchange") or "NSE",
        series=pack.get("series"),
        field=field,
        value=value,
        unit="label",
        session_date=pack.get("session_date"),
        as_of_ist=pack.get("as_of_ist"),
        source=source,
        freshness="fixture" if str(source).startswith("fixture:") else "previous_session",
        detail=detail,
    )


