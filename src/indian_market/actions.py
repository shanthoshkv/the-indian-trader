"""Corporate actions and the results calendar, from announcement rows."""

from __future__ import annotations

from typing import Any

from indian_market.evidence import evidence, missing
from indian_market.records import as_date, done, freshness_for, source_ok
from indian_market.universe import resolve

_KINDS = {"dividend", "split", "bonus", "rights", "buyback", "ofs", "board_meeting"}


def read_actions(pack: dict[str, Any]) -> dict[str, Any]:
    symbol_row = resolve(pack.get("symbol", ""), pack.get("exchange"))
    source = pack.get("source") or "unspecified"
    if not symbol_row["ok"]:
        return {"ok": False, "error": "outside_universe", "detail": symbol_row["detail"]}
    items: list[dict[str, Any]] = []
    if not source_ok(source):
        items.append(
            missing(symbol=symbol_row["symbol"], exchange=symbol_row["exchange"], series=symbol_row.get("series"), field="corporate_action", source=source, detail="Actions need a source.")
        )
        return done(items, symbol=symbol_row["symbol"], exchange=symbol_row["exchange"])
    rows = pack.get("actions") or []
    if not rows:
        items.append(
            missing(
                symbol=symbol_row["symbol"],
                exchange=symbol_row["exchange"],
                series=symbol_row.get("series"),
                field="corporate_action",
                source=source,
                detail="No corporate-action rows were in the announcement file.",
            )
        )
        return done(items, symbol=symbol_row["symbol"], exchange=symbol_row["exchange"])
    for row in rows:
        _one_action(row, items, symbol_row, source, pack.get("as_of_ist"))
    return done(items, symbol=symbol_row["symbol"], exchange=symbol_row["exchange"])


def _one_action(row: dict, items: list, symbol_row: dict, source: str, as_of: str | None) -> None:
    kind = str(row.get("kind") or "").lower()
    row_source = row.get("source") or ""
    symbol = symbol_row["symbol"]
    exchange = symbol_row["exchange"]
    series = symbol_row.get("series")
    if kind not in _KINDS or not source_ok(row_source):
        items.append(
            missing(
                symbol=symbol,
                exchange=exchange,
                series=series,
                field="corporate_action",
                source=row_source or source,
                detail="Kind must be dividend, split, bonus, rights, buyback, ofs, or board_meeting, with a real source.",
            )
        )
        return
    detail = row.get("headline") or kind
    common = dict(
        symbol=symbol,
        exchange=exchange,
        series=series,
        session_date=row.get("session_date"),
        as_of_ist=as_of,
        source=row_source,
        freshness=freshness_for(row_source, "filing"),
        detail=detail,
    )
    items.append(evidence(field="corporate_action", value=kind, unit="label", **common))
    if row.get("ex_date"):
        items.append(evidence(field="ex_date", value=row["ex_date"], unit="date", **common))


def read_results(pack: dict[str, Any]) -> dict[str, Any]:
    source = pack.get("source") or "unspecified"
    as_of = pack.get("as_of")
    watch = [str(symbol).strip() for symbol in (pack.get("watchlist") or []) if str(symbol).strip()]
    items: list[dict[str, Any]] = []
    if not as_of or not source_ok(source) or not watch:
        items.append(missing(symbol="NSE", exchange="NSE", field="results_meeting", source=source, detail="Results need an as-of date, a source, and a watchlist."))
        return done(items, as_of=as_of)

    kept: dict[str, list[dict]] = {}
    for symbol in watch:
        resolved = resolve(symbol, None)
        if not resolved["ok"]:
            items.append(missing(symbol=symbol, exchange="", field="results_meeting", source=source, detail=resolved["detail"]))
            continue
        kept.setdefault(resolved["symbol"], [])
    for row in pack.get("meetings") or []:
        resolved = resolve(row.get("symbol", ""), row.get("exchange"))
        if not resolved["ok"]:
            items.append(missing(symbol=row.get("symbol") or "", exchange=row.get("exchange") or "NSE", field="results_meeting", source=row.get("source") or source, detail=resolved["detail"]))
            continue
        if resolved["symbol"] not in kept:
            continue
        meeting = row.get("meeting_date")
        row_source = row.get("source") or ""
        if not meeting or as_date(meeting) < as_date(as_of) or not source_ok(row_source):
            continue
        kept[resolved["symbol"]].append(row)
        items.append(
            evidence(
                symbol=resolved["symbol"],
                exchange=resolved["exchange"],
                series=resolved.get("series"),
                field="results_meeting",
                value=meeting,
                unit="date",
                session_date=row.get("session_date"),
                as_of_ist=pack.get("as_of_ist"),
                source=row_source,
                freshness=freshness_for(row_source, "filing"),
                detail=row.get("purpose") or "board meeting",
            )
        )
    for symbol, rows in kept.items():
        if rows:
            continue
        resolved = resolve(symbol, None)
        items.append(
            missing(
                symbol=resolved["symbol"],
                exchange=resolved["exchange"],
                series=resolved.get("series"),
                field="results_meeting",
                source=source,
                detail="No board meeting on or after the as-of date was in the announcement file.",
            )
        )
    return done(items, as_of=as_of)
