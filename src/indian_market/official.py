"""Parse an official NSE file the user already has, or try a public URL.

A failed download leaves the field blank. Nothing here places an order.
"""

from __future__ import annotations

import csv
import io
import zipfile
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

from indian_market.evidence import evidence, missing
from indian_market.paths import data_dir
from indian_market.records import done

_KINDS = (
    "cash_bhav",
    "fo_bhav",
    "ban",
    "contract",
    "flows",
    "announcements",
    "delivery",
    "bulk_deals",
    "block_deals",
    "asm",
    "gsm",
    "esm",
    "mwpl",
    "shareholding",
    "pledge",
    "constituents",
)
KINDS = _KINDS


def default_url(kind: str, session: str) -> str:
    ymd = session.replace("-", "")
    if kind == "cash_bhav":
        return f"https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_{ymd}_F_0000.csv.zip"
    if kind == "fo_bhav":
        return f"https://nsearchives.nseindia.com/content/fo/BhavCopy_NSE_FO_0_0_0_{ymd}_F_0000.csv.zip"
    if kind == "ban":
        return f"https://nsearchives.nseindia.com/content/fo/fo_secban_{ymd}.csv"
    if kind == "contract":
        return "https://nsearchives.nseindia.com/content/fo/NSE_FO_contract.csv"
    if kind == "flows":
        return "https://nsearchives.nseindia.com/content/fo/fii_stats.csv"
    if kind == "announcements":
        return "https://nsearchives.nseindia.com/content/equities/announcements.csv"
    return ""


def fetch_official(kind: str, session: str, url: str | None = None) -> dict[str, Any]:
    if kind not in _KINDS:
        return _bad(kind, session, f"Kind is one of {', '.join(_KINDS)}.")
    target = url or default_url(kind, session)
    if not target:
        return _bad(kind, session, "This kind has no default URL. Pass --file or --url.")
    try:
        request = Request(target, headers={"User-Agent": "the-indian-trader/0.1"})
        with urlopen(request, timeout=20) as response:
            raw = response.read()
        cache = data_dir() / "cache"
        cache.mkdir(parents=True, exist_ok=True)
        path = cache / f"{kind}_{session}.csv"
        text = _unzip(raw)
        path.write_text(text, encoding="utf-8")
        return parse_official(kind, path, session, source=target)
    except Exception as exc:  # noqa: BLE001 — a failed public file stays blank
        return _bad(kind, session, f"Download failed. {exc}")


def parse_official(kind: str, path: Path, session: str, source: str) -> dict[str, Any]:
    if kind not in _KINDS:
        return _bad(kind, session, f"Kind is one of {', '.join(_KINDS)}.")
    rows = _table(path)
    items: list[dict[str, Any]] = []
    parser = _PARSERS.get(kind)
    if parser is None:
        return _bad(kind, session, f"Kind is one of {', '.join(_KINDS)}.")
    parser(rows, items, session, source)
    if not items:
        items.append(missing(symbol="NSE", exchange="NSE", field=kind, source=source, detail="The file had no usable rows."))
    return done(items, kind=kind, session_date=session)


def _bad(kind: str, session: str, detail: str) -> dict[str, Any]:
    return {
        "ok": False,
        "error": "no_evidence",
        "kind": kind,
        "session_date": session,
        "detail": detail,
        "items": [missing(symbol="NSE", exchange="NSE", field=kind or "official", source="NSE", detail=detail)],
    }


def _unzip(raw: bytes) -> str:
    if raw[:2] == b"PK":
        archive = zipfile.ZipFile(io.BytesIO(raw))
        name = next(item for item in archive.namelist() if item.lower().endswith(".csv"))
        return archive.read(name).decode("utf-8-sig")
    return raw.decode("utf-8-sig")


def _table(path: Path) -> list[dict[str, str]]:
    text = path.read_text(encoding="utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    rows = []
    for row in reader:
        rows.append({(key or "").strip().lower(): (value or "").strip() for key, value in row.items()})
    return rows


def _num(row: dict[str, str], *keys: str) -> float | None:
    for key in keys:
        raw = row.get(key)
        if raw not in (None, ""):
            return float(raw)
    return None


def _symbol(row: dict[str, str]) -> str:
    return (row.get("tckrsymb") or row.get("symbol") or row.get("ticker") or "").upper()


def _put(items, symbol, field, value, unit, session, source, series=None, detail=None, exchange="NSE") -> None:
    if value is None or symbol == "":
        return
    items.append(
        evidence(
            symbol=symbol,
            exchange=exchange,
            series=series,
            field=field,
            value=value,
            unit=unit,
            session_date=session,
            as_of_ist=None,
            source=source,
            freshness="previous_session" if not str(source).startswith("fixture:") else "fixture",
            detail=detail,
        )
    )


def _cash(rows, items, session, source) -> None:
    for row in rows:
        symbol = _symbol(row)
        series = (row.get("sctysrs") or row.get("series") or "EQ").upper()
        _put(items, symbol, "open", _num(row, "opnpric", "open"), "INR", session, source, series)
        _put(items, symbol, "high", _num(row, "hghpric", "high"), "INR", session, source, series)
        _put(items, symbol, "low", _num(row, "lwpric", "low"), "INR", session, source, series)
        _put(items, symbol, "close", _num(row, "clspric", "close"), "INR", session, source, series)
        _put(items, symbol, "volume", _num(row, "ttltradgvol", "volume"), "units", session, source, series)
        delivery = _num(row, "dlvrypct", "delivery_pct")
        if delivery is None:
            items.append(missing(symbol=symbol or "NSE", exchange="NSE", series=series, field="delivery_pct", source=source, detail="Delivery percent is not in this cash file."))
        else:
            _put(items, symbol, "delivery_pct", delivery, "percent", session, source, series, "Previous session when the file is the bhavcopy.")


def _fo(rows, items, session, source) -> None:
    for row in rows:
        symbol = _symbol(row)
        detail = " ".join(part for part in (row.get("xprydt") or row.get("expiry"), row.get("optntp") or row.get("option_type"), row.get("strkpric") or row.get("strike")) if part)
        _put(items, symbol, "close", _num(row, "clspric", "close"), "INR", session, source, detail=detail or None)
        _put(items, symbol, "open_interest", _num(row, "opnintrst", "oi", "open_interest"), "units", session, source, detail=detail or None)
        _put(items, symbol, "oi_change", _num(row, "chnginopnintrst", "oi_change"), "units", session, source, detail=detail or None)
        _put(items, symbol, "lot_size", _num(row, "newbrdlotqty", "lot_size"), "units", session, source, detail=detail or None)


def _ban(rows, items, session, source) -> None:
    for row in rows:
        symbol = _symbol(row)
        _put(items, symbol, "fo_ban", True, "label", session, source, detail="In the ban file.")


def _contract(rows, items, session, source) -> None:
    for row in rows:
        symbol = _symbol(row)
        detail = row.get("xprydt") or row.get("expiry")
        _put(items, symbol, "lot_size", _num(row, "newbrdlotqty", "lot_size"), "units", session, source, detail=detail)
        _put(items, symbol, "tick_size", _num(row, "ticksize", "tick_size"), "INR", session, source, detail=detail)
        _put(items, symbol, "freeze_qty", _num(row, "freezeqty", "freeze_qty"), "units", session, source, detail=detail)


def _flows(rows, items, session, source) -> None:
    for row in rows:
        name = (row.get("participant") or row.get("symbol") or "").upper()
        _put(items, name or "FII", "flow_net_inr", _num(row, "net_inr", "net"), "INR", row.get("session_date") or session, source, detail=row.get("segment") or "cash")


def _announcements(rows, items, session, source) -> None:
    for row in rows:
        symbol = _symbol(row)
        exchange = _exchange(row)
        _put(items, symbol, "announcement", row.get("headline") or row.get("kind"), "text", session, source, detail=row.get("kind"), exchange=exchange)
        _put(items, symbol, "ex_date", row.get("ex_date") or None, "date", session, source, exchange=exchange)
        _put(items, symbol, "record_date", row.get("record_date") or None, "date", session, source, exchange=exchange)
        _put(items, symbol, "meeting_date", row.get("meeting_date") or None, "date", session, source, exchange=exchange)


def _exchange(row: dict[str, str]) -> str:
    raw = (row.get("exchange") or "NSE").upper()
    if raw in {"NSE", "BSE"}:
        return raw
    return "NSE"


def _delivery(rows, items, session, source) -> None:
    for row in rows:
        symbol = _symbol(row)
        series = (row.get("series") or row.get("sctysrs") or "EQ").upper()
        exchange = _exchange(row)
        _put(items, symbol, "delivery_qty", _num(row, "delivery_qty", "deliv_qty", "deliverable_qty"), "units", session, source, series, exchange=exchange)
        pct = _num(row, "delivery_pct", "deliv_per", "deliverable_pct")
        if pct is None:
            items.append(missing(symbol=symbol or "NSE", exchange=exchange, series=series, field="delivery_pct", source=source, detail="Delivery percent is not in this file."))
        else:
            _put(items, symbol, "delivery_pct", pct, "percent", session, source, series, exchange=exchange)


def _deals(rows, items, session, source, field: str) -> None:
    for row in rows:
        symbol = _symbol(row)
        exchange = _exchange(row)
        client = row.get("client") or row.get("client_name") or ""
        side = (row.get("side") or row.get("buy_sell") or "").lower()
        detail = " ".join(part for part in (side, client) if part) or None
        _put(items, symbol, f"{field}_qty", _num(row, "qty", "quantity"), "units", session, source, detail=detail, exchange=exchange)
        _put(items, symbol, f"{field}_price", _num(row, "price", "trade_price"), "INR", session, source, detail=detail, exchange=exchange)


def _bulk(rows, items, session, source) -> None:
    _deals(rows, items, session, source, "bulk")


def _block(rows, items, session, source) -> None:
    _deals(rows, items, session, source, "block")


def _stage_list(rows, items, session, source, field: str) -> None:
    for row in rows:
        symbol = _symbol(row)
        exchange = _exchange(row)
        stage = row.get("stage") or row.get("grade")
        _put(items, symbol, field, stage or True, "label", session, source, detail="On the list in this file.", exchange=exchange)


def _asm(rows, items, session, source) -> None:
    _stage_list(rows, items, session, source, "asm_stage")


def _gsm(rows, items, session, source) -> None:
    _stage_list(rows, items, session, source, "gsm_stage")


def _esm(rows, items, session, source) -> None:
    _stage_list(rows, items, session, source, "esm_stage")


def _mwpl(rows, items, session, source) -> None:
    for row in rows:
        symbol = _symbol(row)
        exchange = _exchange(row)
        _put(items, symbol, "mwpl", _num(row, "mwpl"), "units", session, source, exchange=exchange)
        pct = _num(row, "oi_pct", "oi_pct_of_mwpl", "current_oi_pct")
        if pct is None:
            items.append(missing(symbol=symbol or "NSE", exchange=exchange, field="oi_pct_of_mwpl", source=source, detail="OI as a percent of MWPL is not in this file."))
        else:
            _put(items, symbol, "oi_pct_of_mwpl", pct, "percent", session, source, exchange=exchange)


def _shareholding(rows, items, session, source) -> None:
    for row in rows:
        symbol = _symbol(row)
        exchange = _exchange(row)
        pct = _num(row, "promoter_pct", "promoter_holding_pct")
        if pct is None:
            items.append(missing(symbol=symbol or "NSE", exchange=exchange, field="promoter_holding_pct", source=source, detail="Promoter holding is not in this file."))
        else:
            _put(items, symbol, "promoter_holding_pct", pct, "percent", session, source, exchange=exchange)


def _pledge(rows, items, session, source) -> None:
    for row in rows:
        symbol = _symbol(row)
        exchange = _exchange(row)
        raw = row.get("pledge_pct")
        if raw is None or raw == "":
            raw = row.get("promoter_pledge_pct")
        if raw is None or str(raw).strip() == "":
            items.append(missing(symbol=symbol or "NSE", exchange=exchange, field="promoter_pledge_pct", source=source, detail="A blank pledge cell is not zero pledge."))
            continue
        _put(items, symbol, "promoter_pledge_pct", float(raw), "percent", session, source, exchange=exchange)


def _constituents(rows, items, session, source) -> None:
    for row in rows:
        symbol = _symbol(row)
        exchange = _exchange(row)
        index = (row.get("index") or row.get("index_name") or "").upper()
        if not symbol or not index:
            items.append(missing(symbol=symbol or "NSE", exchange=exchange, field="index_member", source=source, detail="A constituent row needs an index and a symbol."))
            continue
        _put(items, symbol, "index_member", index, "label", session, source, exchange=exchange)
        weight = _num(row, "weight", "weight_pct")
        if weight is None:
            items.append(missing(symbol=symbol, exchange=exchange, field="weight_pct", source=source, detail="The constituent file has no weight for this name."))
        else:
            _put(items, symbol, "weight_pct", weight, "percent", session, source, detail=index, exchange=exchange)


_PARSERS = {
    "cash_bhav": _cash,
    "fo_bhav": _fo,
    "ban": _ban,
    "contract": _contract,
    "flows": _flows,
    "announcements": _announcements,
    "delivery": _delivery,
    "bulk_deals": _bulk,
    "block_deals": _block,
    "asm": _asm,
    "gsm": _gsm,
    "esm": _esm,
    "mwpl": _mwpl,
    "shareholding": _shareholding,
    "pledge": _pledge,
    "constituents": _constituents,
}
