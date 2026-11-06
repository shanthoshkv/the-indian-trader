"""Resolve a user symbol onto NSE or BSE, or refuse it."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from typing import Any

from indian_market.paths import data_dir

# Names this pack will not treat as Indian cash or equity F&O underlyings.
DENIED = frozenset(
    {
        "AAPL",
        "MSFT",
        "NVDA",
        "GOOGL",
        "GOOG",
        "AMZN",
        "META",
        "TSLA",
        "SPY",
        "QQQ",
        "IWM",
        "DIA",
        "BTC",
        "ETH",
        "SOL",
        "CRUDEOIL",
        "CRUDEOILM",
        "NATURALGAS",
        "NATGAS",
        "SILVERM",
        "GOLDM",
        "COPPER",
    }
)

DENIED_EXCHANGES = frozenset({"MCX", "NCDEX", "NYSE", "NASDAQ", "CRYPTO", "US"})

INDEXES = {
    "NIFTY": {"symbol": "NIFTY", "name": "Nifty 50", "exchange": "NSE", "series": "INDEX"},
    "NIFTY50": {"symbol": "NIFTY", "name": "Nifty 50", "exchange": "NSE", "series": "INDEX"},
    "NIFTY 50": {"symbol": "NIFTY", "name": "Nifty 50", "exchange": "NSE", "series": "INDEX"},
    "BANKNIFTY": {"symbol": "BANKNIFTY", "name": "Nifty Bank", "exchange": "NSE", "series": "INDEX"},
    "BANK NIFTY": {"symbol": "BANKNIFTY", "name": "Nifty Bank", "exchange": "NSE", "series": "INDEX"},
    "NIFTY BANK": {"symbol": "BANKNIFTY", "name": "Nifty Bank", "exchange": "NSE", "series": "INDEX"},
    "FINNIFTY": {"symbol": "FINNIFTY", "name": "Nifty Financial Services", "exchange": "NSE", "series": "INDEX"},
    "FIN NIFTY": {"symbol": "FINNIFTY", "name": "Nifty Financial Services", "exchange": "NSE", "series": "INDEX"},
    "MIDCPNIFTY": {"symbol": "MIDCPNIFTY", "name": "Nifty Midcap Select", "exchange": "NSE", "series": "INDEX"},
    "SENSEX": {"symbol": "SENSEX", "name": "S&P BSE Sensex", "exchange": "BSE", "series": "INDEX"},
    "BSESENSEX": {"symbol": "SENSEX", "name": "S&P BSE Sensex", "exchange": "BSE", "series": "INDEX"},
    "BANKEX": {"symbol": "BANKEX", "name": "S&P BSE Bankex", "exchange": "BSE", "series": "INDEX"},
    "INDIAVIX": {"symbol": "INDIAVIX", "name": "India VIX", "exchange": "NSE", "series": "INDEX"},
    "INDIA VIX": {"symbol": "INDIAVIX", "name": "India VIX", "exchange": "NSE", "series": "INDEX"},
}

_SYMBOL = re.compile(r"^[A-Z0-9][A-Z0-9&-]{0,19}$")
_BSE_CODE = re.compile(r"^\d{6}$")


@lru_cache(maxsize=1)
def _book() -> dict[str, dict[str, Any]]:
    payload = json.loads((data_dir() / "symbols.json").read_text(encoding="utf-8"))
    return {row["symbol"]: row for row in payload["symbols"]}


def _fail(detail: str) -> dict[str, Any]:
    return {"ok": False, "error": "outside_universe", "detail": detail}


def resolve(raw: str, exchange: str | None = None) -> dict[str, Any]:
    """Map a user token to NSE or BSE. Exit-code 2 material when ok is false."""
    text = (raw or "").strip().upper()
    if not text:
        return _fail("No symbol was given.")

    forced = exchange.upper().strip() if exchange else None
    if forced in DENIED_EXCHANGES:
        return _fail(f"{forced} is outside this pack. Use NSE or BSE.")

    if text.endswith(".NS"):
        text = text[:-3]
        forced = forced or "NSE"
    elif text.endswith(".BO"):
        text = text[:-3]
        forced = forced or "BSE"

    if text in DENIED:
        return _fail(f"{text} is not an NSE or BSE symbol in this pack.")

    index = INDEXES.get(text)
    if index:
        if forced and forced != index["exchange"]:
            return _fail(
                f"{index['symbol']} is listed as an index on {index['exchange']}, not {forced}."
            )
        return {"ok": True, "verified": True, "instrument": "index", "bse_code": None, **index}

    if _BSE_CODE.match(text):
        for row in _book().values():
            if row.get("bse_code") == text:
                return _from_row(row, "BSE", verified=True)
        if forced == "NSE":
            return _fail(f"{text} looks like a BSE scrip code, not an NSE symbol.")
        return {
            "ok": True,
            "verified": False,
            "instrument": "equity",
            "symbol": text,
            "name": None,
            "exchange": "BSE",
            "series": "EQ",
            "bse_code": text,
            "detail": "Scrip code is not in the starter book. Confirm it on the BSE quote page before use.",
        }

    if not _SYMBOL.match(text):
        return _fail(f"{raw.strip()} is not an NSE or BSE symbol.")

    row = _book().get(text)
    if row:
        use_exchange = forced or "NSE"
        if use_exchange == "BSE" and not row.get("bse_code"):
            return _fail(f"{text} has no BSE code in the starter book.")
        if use_exchange not in {"NSE", "BSE"}:
            return _fail(f"{use_exchange} is outside this pack. Use NSE or BSE.")
        return _from_row(row, use_exchange, verified=True)

    if forced == "BSE":
        return _fail(f"{text} is not in the starter book as a BSE name. Pass the 6-digit scrip code.")

    return {
        "ok": True,
        "verified": False,
        "instrument": "equity",
        "symbol": text,
        "name": None,
        "exchange": "NSE",
        "series": "EQ",
        "bse_code": None,
        "detail": "Not in the starter book. Confirm the symbol against the NSE security file before a trade.",
    }


def _from_row(row: dict[str, Any], exchange: str, *, verified: bool) -> dict[str, Any]:
    return {
        "ok": True,
        "verified": verified,
        "instrument": "equity",
        "symbol": row["symbol"],
        "name": row["name"],
        "exchange": exchange,
        "series": row.get("series") or "EQ",
        "bse_code": row.get("bse_code"),
    }
