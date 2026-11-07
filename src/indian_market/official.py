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

_KINDS = ("cash_bhav", "fo_bhav", "ban", "contract", "flows", "announcements")


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
    return "https://nsearchives.nseindia.com/content/equities/announcements.csv"


def fetch_official(kind: str, session: str, url: str | None = None) -> dict[str, Any]:
    if kind not in _KINDS:
        return _bad(kind, session, f"Kind is one of {', '.join(_KINDS)}.")
    target = url or default_url(kind, session)
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
    if kind == "cash_bhav":
        _cash(rows, items, session, source)
    elif kind == "fo_bhav":
        _fo(rows, items, session, source)
    elif kind == "ban":
        _ban(rows, items, session, source)
    elif kind == "contract":
        _contract(rows, items, session, source)
    elif kind == "flows":
        _flows(rows, items, session, source)
    else:
        _announcements(rows, items, session, source)
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


def _put(items, symbol, field, value, unit, session, source, series=None, detail=None) -> None:
    if value is None or symbol == "":
        return
    items.append(
        evidence(
            symbol=symbol,
            exchange="NSE",
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
        _put(items, symbol, "announcement", row.get("headline") or row.get("kind"), "text", session, source, detail=row.get("kind"))
        _put(items, symbol, "ex_date", row.get("ex_date") or None, "date", session, source)
        _put(items, symbol, "record_date", row.get("record_date") or None, "date", session, source)
        _put(items, symbol, "meeting_date", row.get("meeting_date") or None, "date", session, source)
