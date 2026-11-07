"""Quotes the user already located. Guidance, capex, and what was declined.

A topic with no sourced excerpt stays blank. The text is not paraphrased here.
"""

from __future__ import annotations

from typing import Any

from indian_market.evidence import evidence, missing
from indian_market.records import done, freshness_for, source_ok

TOPICS = ("guidance", "capex", "declined")


def read_concall(pack: dict[str, Any]) -> dict[str, Any]:
    symbol = pack["symbol"]
    exchange = pack["exchange"]
    series = pack.get("series")
    source = pack.get("source") or "unspecified"
    session = pack.get("session_date")
    as_of = pack.get("as_of_ist")
    items: list[dict[str, Any]] = []
    if not source_ok(source):
        items.append(missing(symbol=symbol, exchange=exchange, series=series, field="concall", source=source, detail="The transcript pack needs a source."))
        return done(items, symbol=symbol, exchange=exchange, series=series)

    counts = {topic: 0 for topic in TOPICS}
    for row in pack.get("excerpts") or []:
        topic = str(row.get("topic") or "").lower()
        row_source = row.get("source") or ""
        if topic not in TOPICS:
            continue
        if not row.get("text") or not source_ok(row_source):
            items.append(
                missing(
                    symbol=symbol,
                    exchange=exchange,
                    series=series,
                    field=topic,
                    source=row_source or source,
                    detail="An excerpt needs text and an NSE, BSE, http, or fixture source.",
                )
            )
            continue
        speaker = row.get("speaker")
        items.append(
            evidence(
                symbol=symbol,
                exchange=exchange,
                series=series,
                field=topic,
                value=row["text"],
                unit="text",
                session_date=session,
                as_of_ist=as_of,
                source=row_source,
                freshness=freshness_for(row_source, "filing"),
                detail=speaker or pack.get("fiscal_period"),
            )
        )
        counts[topic] += 1

    blanks = {
        "guidance": "No guidance excerpt was in the transcript pack.",
        "capex": "No capex excerpt was in the transcript pack.",
        "declined": "No excerpt where management declined to answer. Do not invent one.",
    }
    for topic in TOPICS:
        if counts[topic] == 0:
            items.append(missing(symbol=symbol, exchange=exchange, series=series, field=topic, source=source, detail=blanks[topic]))
    return done(items, symbol=symbol, exchange=exchange, series=series, fiscal_period=pack.get("fiscal_period"))
