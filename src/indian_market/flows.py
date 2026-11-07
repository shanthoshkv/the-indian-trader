"""FII, DII, participant open interest, and bulk or block deals.

Every cash and open-interest row is previous_session. The file's session
date is the date the figure belongs to.
"""

from __future__ import annotations

from typing import Any

from indian_market.evidence import evidence, missing
from indian_market.records import done, source_ok
from indian_market.universe import resolve

_PARTICIPANTS = {"FII": "FII", "FPI": "FII", "DII": "DII", "PRO": "PRO", "CLIENT": "CLIENT"}
_LEGS = (
    ("future_long_oi", "future_long"),
    ("future_short_oi", "future_short"),
    ("call_long_oi", "call_long"),
    ("call_short_oi", "call_short"),
    ("put_long_oi", "put_long"),
    ("put_short_oi", "put_short"),
)


def read_flows(pack: dict[str, Any]) -> dict[str, Any]:
    source = pack.get("source") or "unspecified"
    session = pack.get("session_date")
    as_of = pack.get("as_of_ist")
    items: list[dict[str, Any]] = []
    if not session or not source_ok(source):
        items.append(
            missing(
                symbol="NSE",
                exchange="NSE",
                field="flows",
                source=source,
                detail="Flows need a session date and an NSE, BSE, http, or fixture source.",
            )
        )
        return done(items, session_date=session)

    for field, key, symbol in (
        ("fii_cash_net", "fii_cash_crore", "FII"),
        ("dii_cash_net", "dii_cash_crore", "DII"),
    ):
        value = (pack.get("cash") or {}).get(key)
        if value is None:
            items.append(missing(symbol=symbol, exchange="NSE", series="CASH", field=field, source=source, detail="Not in the cash file."))
            continue
        items.append(
            evidence(
                symbol=symbol,
                exchange="NSE",
                series="CASH",
                field=field,
                value=value,
                unit="INR_crore",
                session_date=session,
                as_of_ist=as_of,
                source=source,
                freshness="previous_session",
            )
        )

    for row in pack.get("participant_oi") or []:
        name = _PARTICIPANTS.get(str(row.get("participant", "")).upper())
        if name is None:
            items.append(
                missing(
                    symbol=str(row.get("participant") or ""),
                    exchange="NSE",
                    series="PARTICIPANT",
                    field="participant_oi",
                    source=source,
                    detail="Participant must be FII, FPI, DII, Pro, or Client.",
                )
            )
            continue
        for field, key in _LEGS:
            if row.get(key) is None:
                continue
            items.append(
                evidence(
                    symbol=name,
                    exchange="NSE",
                    series="PARTICIPANT",
                    field=field,
                    value=row[key],
                    unit="contracts",
                    session_date=session,
                    as_of_ist=as_of,
                    source=source,
                    freshness="previous_session",
                )
            )

    for row in pack.get("deals") or []:
        _deal(row, items, source, session, as_of)

    if not any(item["field"] != "flows" for item in items):
        items.append(missing(symbol="NSE", exchange="NSE", field="flows", source=source, detail="The file had no cash, participant, or deal rows."))
    return done(items, session_date=session)


def _deal(row: dict[str, Any], items: list, source: str, session: str, as_of: str | None) -> None:
    kind = str(row.get("kind") or "").lower()
    resolved = resolve(row.get("symbol", ""), row.get("exchange"))
    if kind not in {"bulk", "block"}:
        items.append(
            missing(symbol=row.get("symbol") or "", exchange=row.get("exchange") or "NSE", field="deal_qty", source=source, detail="Deal kind must be bulk or block.")
        )
        return
    if not resolved["ok"]:
        items.append(missing(symbol=row.get("symbol") or "", exchange=row.get("exchange") or "NSE", field="deal_qty", source=source, detail=resolved["detail"]))
        return
    if row.get("qty") is None or row.get("price") is None:
        items.append(
            missing(
                symbol=resolved["symbol"],
                exchange=resolved["exchange"],
                series=resolved.get("series"),
                field="deal_qty",
                source=source,
                detail="A deal needs quantity and price.",
            )
        )
        return
    detail = f"{kind} deal"
    if row.get("client"):
        detail = f"{detail}; client={row['client']}"
    common = dict(
        symbol=resolved["symbol"],
        exchange=resolved["exchange"],
        series=resolved.get("series"),
        session_date=session,
        as_of_ist=as_of,
        source=source,
        freshness="previous_session",
        detail=detail,
    )
    items.append(evidence(field="deal_qty", value=row["qty"], unit="shares", **common))
    items.append(evidence(field="deal_price", value=row["price"], unit="INR", **common))
