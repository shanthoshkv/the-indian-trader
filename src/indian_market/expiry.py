"""Equity F&O expiry dates. Weekly contracts exist only for Nifty and Sensex."""

from __future__ import annotations

from datetime import date, timedelta

from indian_market.calendar_in import is_trading_day, previous_trading_day

# Weekly weekday: Monday is 0.
WEEKLY = {
    "NIFTY": {"exchange": "NSE", "weekday": 1, "weekly": True},
    "SENSEX": {"exchange": "BSE", "weekday": 3, "weekly": True},
    "BANKNIFTY": {"exchange": "NSE", "weekday": 1, "weekly": False},
    "FINNIFTY": {"exchange": "NSE", "weekday": 1, "weekly": False},
    "MIDCPNIFTY": {"exchange": "NSE", "weekday": 1, "weekly": False},
    "BANKEX": {"exchange": "BSE", "weekday": 3, "weekly": False},
}

_ALIASES = {
    "NIFTY": "NIFTY",
    "NIFTY50": "NIFTY",
    "BANKNIFTY": "BANKNIFTY",
    "BANK NIFTY": "BANKNIFTY",
    "FINNIFTY": "FINNIFTY",
    "MIDCPNIFTY": "MIDCPNIFTY",
    "SENSEX": "SENSEX",
    "BANKEX": "BANKEX",
    "STOCK": "NIFTY",
}


def _shift(day: date, exchange: str) -> date:
    if is_trading_day(day, exchange):
        return day
    return previous_trading_day(day, exchange)


def _nth_weekday(year: int, month: int, weekday: int, last: bool = False) -> date:
    if last:
        if month == 12:
            cursor = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            cursor = date(year, month + 1, 1) - timedelta(days=1)
        while cursor.weekday() != weekday:
            cursor -= timedelta(days=1)
        return cursor
    cursor = date(year, month, 1)
    while cursor.weekday() != weekday:
        cursor += timedelta(days=1)
    return cursor


def _weekly_on_or_after(on: date, weekday: int, exchange: str) -> date:
    for offset in range(0, 21):
        day = on + timedelta(days=offset)
        if day.weekday() != weekday:
            continue
        expiry = _shift(day, exchange)
        if expiry >= on:
            return expiry
    raise RuntimeError("no weekly expiry in the search window")


def _monthly_on_or_after(on: date, weekday: int, exchange: str) -> date:
    year, month = on.year, on.month
    for _ in range(3):
        raw = _nth_weekday(year, month, weekday, last=True)
        expiry = _shift(raw, exchange)
        if expiry >= on:
            return expiry
        month += 1
        if month == 13:
            month = 1
            year += 1
    raise RuntimeError("no monthly expiry in the search window")


def next_expiry(symbol: str, on: date | str) -> dict:
    key = _ALIASES.get(symbol.strip().upper())
    if key is None:
        return {
            "ok": False,
            "error": "outside_universe",
            "detail": f"{symbol} has no expiry rule in this pack. Pass NIFTY, BANKNIFTY, SENSEX, or BANKEX.",
        }
    rule = WEEKLY[key]
    on_date = date.fromisoformat(on) if isinstance(on, str) else on
    monthly = _monthly_on_or_after(on_date, rule["weekday"], rule["exchange"])
    weekly = (
        _weekly_on_or_after(on_date, rule["weekday"], rule["exchange"]) if rule["weekly"] else None
    )
    return {
        "ok": True,
        "symbol": key,
        "exchange": rule["exchange"],
        "as_of": on_date.isoformat(),
        "weekly": None if weekly is None else weekly.isoformat(),
        "monthly": monthly.isoformat(),
        "detail": None
        if rule["weekly"]
        else f"{key} has no weekly contract. The next expiry is the monthly.",
    }
