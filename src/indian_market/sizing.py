"""Quantity from rupee risk. Charges come from the dated sheet. This is not an order."""

from __future__ import annotations

import math
from datetime import date
from typing import Any

from indian_market.costs import charge_rate
from indian_market.evidence import evidence, missing
from indian_market.plan import HORIZONS
from indian_market.records import as_date, done, source_ok

_STT = {
    "intraday_cash": ("stt_equity_intraday_sell",),
    "delivery": ("stt_equity_delivery_buy", "stt_equity_delivery_sell"),
    "futures": ("stt_fut_sell",),
    "options": ("stt_opt_premium_sell",),
}
_EXCHANGE = {
    "intraday_cash": "nse_txn_equity",
    "delivery": "nse_txn_equity",
    "futures": "nse_txn_futures",
    "options": "nse_txn_options_premium",
}


def size_position(pack: dict[str, Any]) -> dict[str, Any]:
    symbol = pack["symbol"]
    exchange = pack["exchange"]
    series = pack.get("series")
    source = pack.get("source") or "unspecified"
    session = pack.get("session_date")
    as_of = pack.get("as_of_ist")
    on = as_date(pack["as_of"]) if pack.get("as_of") else (as_date(session) if session else date.today())
    items: list[dict[str, Any]] = []
    common = dict(
        symbol=symbol,
        exchange=exchange,
        series=series,
        session_date=session,
        as_of_ist=as_of,
        source="data/costs.json" if source_ok(source) else source,
        freshness="filing",
    )
    if pack.get("plan_status") not in {None, "ready"}:
        items.append(missing(symbol=symbol, exchange=exchange, series=series, field="quantity", source=source, detail=f"Plan status is {pack.get('plan_status')}. Only a ready plan is sized."))
        return done(items, symbol=symbol, exchange=exchange, series=series)
    horizon = pack.get("horizon")
    if horizon not in HORIZONS:
        items.append(missing(symbol=symbol, exchange=exchange, series=series, field="quantity", source=source, detail="Horizon is intraday_cash, delivery, futures, or options."))
        return done(items, symbol=symbol, exchange=exchange, series=series)
    if horizon in {"futures", "options"} and (pack.get("clearance") == "blocked" or pack.get("fo_ban")):
        items.append(missing(symbol=symbol, exchange=exchange, series=series, field="quantity", source=source, detail="Fresh F&O is blocked. No quantity."))
        return done(items, symbol=symbol, exchange=exchange, series=series)
    if horizon == "intraday_cash" and (pack.get("trade_for_trade") or str(series or "").upper() == "BE"):
        items.append(missing(symbol=symbol, exchange=exchange, series=series, field="quantity", source=source, detail="This series is trade for trade. Intraday quantity is not available."))
        return done(items, symbol=symbol, exchange=exchange, series=series)

    entry, stop, risk, lot = pack.get("entry"), pack.get("invalidation"), pack.get("risk_inr"), pack.get("lot_size")
    if entry is None or stop is None or risk is None or not lot:
        items.append(missing(symbol=symbol, exchange=exchange, series=series, field="quantity", source=source, detail="Entry, invalidation, risk in rupees, and lot size are required. Do not hardcode the lot."))
        return done(items, symbol=symbol, exchange=exchange, series=series)
    distance = abs(entry - stop)
    if distance == 0 or risk <= 0 or lot <= 0:
        items.append(missing(symbol=symbol, exchange=exchange, series=series, field="quantity", source=source, detail="Risk distance and lot size have to be above zero."))
        return done(items, symbol=symbol, exchange=exchange, series=series)
    quantity = math.floor((risk / distance) / lot) * lot
    items.append(
        evidence(
            field="quantity",
            value=int(quantity),
            unit="units",
            detail="Floored to the lot. Price risk only. Charges are not an order and are not deducted from this quantity.",
            **{**common, "source": source, "freshness": "fixture" if source.startswith("fixture:") else "previous_session"},
        )
    )
    _charges(items, common, horizon, entry, quantity, on, pack.get("brokerage_inr"), symbol, exchange, series, source)
    return done(items, symbol=symbol, exchange=exchange, series=series)


def _charges(items, common, horizon, entry, quantity, on, brokerage, symbol, exchange, series, source) -> None:
    if quantity == 0:
        items.append(missing(symbol=symbol, exchange=exchange, series=series, field="stt_inr", source="data/costs.json", detail="Quantity is zero, so STT was not estimated."))
        return
    rates = []
    for item_id in _STT[horizon]:
        found = charge_rate(item_id, on)
        if not found["ok"]:
            items.append(missing(symbol=symbol, exchange=exchange, series=series, field="stt_inr", source="data/costs.json", detail=found["detail"]))
            return
        rates.append(found)
    notional = abs(entry) * quantity
    if horizon == "delivery":
        stt = notional * rates[0]["rate"] + notional * rates[1]["rate"]
        detail = "Delivery STT on both sides, both estimated at the entry price."
    else:
        stt = notional * rates[0]["rate"]
        detail = "Sell-side STT estimated at the entry price. The exit is not known yet."
    items.append(evidence(field="stt_inr", value=round(stt, 2), unit="INR", detail=detail, **common))
    exchange_inr = _turnover_charge(items, common, _EXCHANGE[horizon], "exchange_txn_inr", notional, on, symbol, exchange, series, exchange == "NSE")
    _turnover_charge(items, common, "sebi_turnover", "sebi_inr", notional, on, symbol, exchange, series, True)
    stamp = charge_rate("stamp_duty", on)
    items.append(missing(symbol=symbol, exchange=exchange, series=series, field="stamp_inr", source="data/costs.json", detail=stamp["detail"]))
    if brokerage is None:
        items.append(missing(symbol=symbol, exchange=exchange, series=series, field="gst_inr", source="data/costs.json", detail="No brokerage was supplied. GST was not invented."))
        return
    gst = charge_rate("gst_on_brokerage_and_charges", on)
    if not gst["ok"]:
        items.append(missing(symbol=symbol, exchange=exchange, series=series, field="gst_inr", source="data/costs.json", detail=gst["detail"]))
        return
    base = brokerage + (exchange_inr or 0)
    gst_detail = "GST on brokerage plus the exchange transaction charge. GST is not charged on STT."
    if exchange_inr is None:
        gst_detail = "GST on the brokerage supplied. The exchange transaction charge was blank, so it is not in this GST figure. GST is not charged on STT."
    items.append(evidence(field="gst_inr", value=round(base * gst["rate"], 2), unit="INR", detail=gst_detail, **common))


def _turnover_charge(items, common, item_id, field, notional, on, symbol, exchange, series, apply: bool):
    """Both sides estimated at the entry price. Exit is not known yet. Returns the rupee amount, or None."""
    if not apply:
        items.append(missing(symbol=symbol, exchange=exchange, series=series, field=field, source="data/costs.json", detail="No BSE transaction rate is on the charge sheet."))
        return None
    found = charge_rate(item_id, on)
    if not found["ok"]:
        items.append(missing(symbol=symbol, exchange=exchange, series=series, field=field, source="data/costs.json", detail=found["detail"]))
        return None
    amount = round(notional * found["rate"] * 2, 2)
    items.append(evidence(field=field, value=amount, unit="INR", detail="Both sides, both estimated at the entry price. Not deducted from quantity.", **common))
    return amount
