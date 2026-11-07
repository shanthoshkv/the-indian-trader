"""Round trips with the dated charge sheet, slippage in ticks, and expiry week.

A run that does not include STT fails. Slippage is applied to the fill.
It is not optional, though the pack may set slippage_ticks to zero.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from indian_market.costs import charge_rate, stamp_rate
from indian_market.evidence import evidence, missing
from indian_market.expiry import next_expiry
from indian_market.records import as_date, done, source_ok

_STT = {
    "intraday_cash": ("stt_equity_intraday_sell",),
    "delivery": ("stt_equity_delivery_buy", "stt_equity_delivery_sell"),
    "futures": ("stt_fut_sell",),
    "options": ("stt_opt_premium_sell",),
}
_STAMP = {
    "intraday_cash": "stamp_equity_intraday",
    "delivery": "stamp_equity_delivery",
    "futures": "stamp_futures",
    "options": "stamp_options_premium",
}


def run_backtest(pack: dict[str, Any]) -> dict[str, Any]:
    symbol = pack["symbol"]
    exchange = pack["exchange"]
    series = pack.get("series")
    source = pack.get("source") or "unspecified"
    horizon = pack.get("horizon")
    items: list[dict[str, Any]] = []
    if pack.get("include_stt") is not True:
        return {
            "ok": False,
            "error": "stt_required",
            "symbol": symbol,
            "exchange": exchange,
            "detail": "A backtest that ignores STT fails. Set include_stt to true and use data/costs.json.",
            "items": [
                missing(symbol=symbol, exchange=exchange, series=series, field="net_pnl_inr", source="data/costs.json", detail="STT was not included.")
            ],
        }
    if horizon not in _STT:
        items.append(missing(symbol=symbol, exchange=exchange, series=series, field="net_pnl_inr", source=source, detail="Horizon is intraday_cash, delivery, futures, or options."))
        return done(items, symbol=symbol, exchange=exchange)
    if "slippage_ticks" not in pack or pack.get("tick_size") in (None, 0):
        items.append(missing(symbol=symbol, exchange=exchange, series=series, field="slippage_inr", source=source, detail="Tick size and slippage_ticks are required. Zero ticks is allowed only when the pack says 0."))
        return done(items, symbol=symbol, exchange=exchange)
    if not source_ok(source) or not pack.get("trades"):
        items.append(missing(symbol=symbol, exchange=exchange, series=series, field="net_pnl_inr", source=source, detail="The run needs a source and at least one trade."))
        return done(items, symbol=symbol, exchange=exchange)

    slip = float(pack["slippage_ticks"]) * float(pack["tick_size"])
    actions = pack.get("actions")
    buyer_state = pack.get("buyer_state")
    total_net = 0.0
    total_stt = 0.0
    total_slip = 0.0
    total_exchange = 0.0
    total_stamp = 0.0
    exchange_blank = False
    stamp_blank = False
    expiry_hits = 0
    nets: list[float] = []
    by_horizon: dict[str, float] = {}
    for index, trade in enumerate(pack["trades"], start=1):
        trade_horizon = trade.get("horizon") or horizon
        scored = _trade(symbol, exchange, series, trade_horizon, trade, slip, source, actions, buyer_state)
        if not scored["ok"]:
            items.append(missing(symbol=symbol, exchange=exchange, series=series, field="trade_net_pnl_inr", source="data/costs.json", detail=scored["detail"]))
            return done(items, symbol=symbol, exchange=exchange)
        total_net += scored["net"]
        total_stt += scored["stt"]
        total_slip += scored["slippage"]
        if scored["exchange_txn"] is None:
            exchange_blank = True
        else:
            total_exchange += scored["exchange_txn"]
        if buyer_state:
            if scored["stamp"] is None:
                stamp_blank = True
            else:
                total_stamp += scored["stamp"]
        nets.append(scored["net"])
        by_horizon[trade_horizon] = by_horizon.get(trade_horizon, 0.0) + scored["net"]
        if scored["expiry_week"]:
            expiry_hits += 1
        common = dict(symbol=symbol, exchange=exchange, series=series, session_date=scored["session"], as_of_ist=None, source="data/costs.json", freshness="filing")
        items.append(evidence(field="trade_net_pnl_inr", value=round(scored["net"], 2), unit="INR", detail=f"trade {index} {trade_horizon}", **common))
        items.append(evidence(field="expiry_week", value=scored["expiry_week"], unit="label", detail=scored["expiry_detail"], **common))
    summary = dict(symbol=symbol, exchange=exchange, series=series, session_date=pack.get("as_of"), as_of_ist=None, source="data/costs.json", freshness="filing")
    items.append(evidence(field="net_pnl_inr", value=round(total_net, 2), unit="INR", detail="After slippage in the fill and STT. Exchange transaction charges and GST are quoted beside this net.", **summary))
    items.append(evidence(field="stt_inr", value=round(total_stt, 2), unit="INR", **summary))
    items.append(evidence(field="slippage_inr", value=round(total_slip, 2), unit="INR", detail=f"{pack['slippage_ticks']} ticks of {pack['tick_size']}", **summary))
    if exchange_blank:
        items.append(missing(symbol=symbol, exchange=exchange, series=series, field="exchange_txn_inr", source="data/costs.json", detail="Exchange transaction charge was not on the sheet for every fill."))
    else:
        items.append(evidence(field="exchange_txn_inr", value=round(total_exchange, 2), unit="INR", detail="Both sides on the adjusted fills. Not inside net_pnl_inr.", **summary))
    if buyer_state:
        if stamp_blank:
            items.append(missing(symbol=symbol, exchange=exchange, series=series, field="stamp_inr", source="data/costs.json", detail="Stamp duty could not be priced for every fill. It is not inside net_pnl_inr."))
        else:
            items.append(evidence(field="stamp_inr", value=round(total_stamp, 2), unit="INR", detail=f"Buy-side stamp for {buyer_state}. Not inside net_pnl_inr.", **summary))
    items.append(evidence(field="max_drawdown_inr", value=round(_drawdown(nets), 2), unit="INR", detail="Peak to trough of the cumulative net, in trade order.", **summary))
    items.append(evidence(field="expiry_week_count", value=expiry_hits, unit="count", **summary))
    for name, total in by_horizon.items():
        items.append(evidence(field="horizon_net_pnl_inr", value=round(total, 2), unit="INR", detail=name, **summary))
    return done(items, symbol=symbol, exchange=exchange, series=series)


def _trade(symbol, exchange, series, horizon, trade, slip, source, actions, buyer_state) -> dict[str, Any]:
    if None in (trade.get("entry"), trade.get("exit"), trade.get("qty"), trade.get("exit_time")):
        return {"ok": False, "detail": "A trade needs entry, exit, qty, and exit_time."}
    side = trade.get("side") or "long"
    if side not in {"long", "short"}:
        return {"ok": False, "detail": "Trade side is long or short."}
    if horizon not in _STT:
        return {"ok": False, "detail": "Trade horizon is intraday_cash, delivery, futures, or options."}
    adjusted = _adjusted(trade, actions)
    if adjusted["error"]:
        return {"ok": False, "detail": adjusted["error"]}
    on = as_date(trade["exit_time"])
    signed = slip if side == "long" else -slip
    entry = adjusted["entry"] + signed
    exit_ = adjusted["exit"] - signed
    qty = trade["qty"]
    gross = (exit_ - entry) * qty if side == "long" else (entry - exit_) * qty
    slippage = abs(slip) * qty * 2
    stt = _stt(horizon, side, entry, exit_, qty, on)
    if not stt["ok"]:
        return stt
    net = gross - stt["amount"]
    exchange_txn = _exchange_txn(horizon, exchange, entry, exit_, qty, on)
    brokerage = trade.get("brokerage_inr")
    if brokerage is not None:
        gst = charge_rate("gst_on_brokerage_and_charges", on)
        if not gst["ok"]:
            return gst
        net -= brokerage * gst["rate"]
    week = _expiry_week(symbol, on, trade.get("expiry_date"))
    stamp = None
    if buyer_state:
        stamped = _stamp(horizon, side, entry, exit_, qty, on, buyer_state)
        if stamped["ok"]:
            stamp = stamped["amount"]
    return {
        "ok": True,
        "net": net,
        "stt": stt["amount"],
        "exchange_txn": exchange_txn,
        "stamp": stamp,
        "slippage": slippage,
        "session": on.isoformat(),
        "expiry_week": week["expiry_week"],
        "expiry_detail": week["detail"],
    }


def _adjusted(trade: dict[str, Any], actions) -> dict[str, Any]:
    """Apply a supplied price_factor to legs strictly before ex_date. Slippage comes later."""
    entry = float(trade["entry"])
    exit_ = float(trade["exit"])
    if not actions:
        return {"entry": entry, "exit": exit_, "error": None}
    if not trade.get("entry_time"):
        return {"entry": entry, "exit": exit_, "error": "A corporate action needs entry_time. Prices were not adjusted."}
    entry_day = as_date(trade["entry_time"])
    exit_day = as_date(trade["exit_time"])
    for action in actions:
        factor = action.get("price_factor")
        ex = action.get("ex_date")
        if factor is None or ex in (None, ""):
            return {"entry": entry, "exit": exit_, "error": "A corporate action needs a numeric price_factor and an ex_date. Prices were not adjusted."}
        try:
            factor = float(factor)
        except (TypeError, ValueError):
            return {"entry": entry, "exit": exit_, "error": "A corporate action needs a numeric price_factor and an ex_date. Prices were not adjusted."}
        ex_day = as_date(ex)
        if entry_day < ex_day:
            entry *= factor
        if exit_day < ex_day:
            exit_ *= factor
    return {"entry": entry, "exit": exit_, "error": None}


def _stt(horizon: str, side: str, entry: float, exit_: float, qty: float, on: date) -> dict[str, Any]:
    ids = _STT[horizon]
    rates = []
    for item_id in ids:
        found = charge_rate(item_id, on)
        if not found["ok"]:
            return found
        rates.append(found["rate"])
    if horizon == "delivery":
        buy = entry if side == "long" else exit_
        sell = exit_ if side == "long" else entry
        amount = abs(buy) * qty * rates[0] + abs(sell) * qty * rates[1]
    else:
        sell = exit_ if side == "long" else entry
        amount = abs(sell) * qty * rates[0]
    return {"ok": True, "amount": amount}


def _drawdown(nets: list[float]) -> float:
    equity = 0.0
    peak = 0.0
    worst = 0.0
    for net in nets:
        equity += net
        peak = max(peak, equity)
        worst = max(worst, peak - equity)
    return worst


def _stamp(horizon: str, side: str, entry: float, exit_: float, qty: float, on: date, state: str) -> dict[str, Any]:
    found = stamp_rate(_STAMP[horizon], state, on)
    if not found["ok"]:
        return found
    buy = entry if side == "long" else exit_
    return {"ok": True, "amount": abs(buy) * qty * found["rate"]}


def _exchange_txn(horizon: str, exchange: str, entry: float, exit_: float, qty: float, on: date) -> float | None:
    if exchange == "NSE":
        item_id = {
            "intraday_cash": "nse_txn_equity",
            "delivery": "nse_txn_equity",
            "futures": "nse_txn_futures",
            "options": "nse_txn_options_premium",
        }[horizon]
    elif exchange == "BSE" and horizon in {"intraday_cash", "delivery"}:
        item_id = "bse_txn_equity"
    else:
        return None
    found = charge_rate(item_id, on)
    if not found["ok"]:
        return None
    return (abs(entry) + abs(exit_)) * qty * found["rate"]


def _expiry_week(symbol: str, day: date, explicit: str | None) -> dict[str, Any]:
    if explicit:
        expiry = as_date(explicit)
        flag = expiry.isocalendar()[:2] == day.isocalendar()[:2]
        return {"expiry_week": flag, "detail": f"Trade date compared with expiry_date {explicit}."}
    found = next_expiry(symbol, day.isoformat())
    if not found.get("ok"):
        return {"expiry_week": False, "detail": "No index expiry rule for this symbol. Pass expiry_date on the trade to call the week out."}
    for raw in (found.get("weekly"), found.get("monthly")):
        if raw and as_date(raw).isocalendar()[:2] == day.isocalendar()[:2]:
            return {"expiry_week": True, "detail": f"Same ISO week as {raw}."}
    return {"expiry_week": False, "detail": "Not the ISO week of the next weekly or monthly expiry."}
