"""Advance, decline, highs, lows, and whether a few names carry the index.

Only fields present in the pack are scored. Concentration is narrow when
the largest absolute point contribution is at least 40 percent of the total.
"""

from __future__ import annotations

from typing import Any

from indian_market.evidence import evidence, missing
from indian_market.records import done, source_ok
from indian_market.universe import resolve

_NARROW_SHARE = 0.40


def read_breadth(pack: dict[str, Any]) -> dict[str, Any]:
    exchange = str(pack.get("exchange") or "").upper()
    if exchange not in {"NSE", "BSE"}:
        return {
            "ok": False,
            "error": "outside_universe",
            "detail": f"{exchange or 'missing exchange'} is outside this pack. Breadth is NSE or BSE.",
        }
    source = pack.get("source") or "unspecified"
    session = pack.get("session_date")
    as_of = pack.get("as_of_ist")
    freshness = "previous_session"
    items: list[dict[str, Any]] = []
    if not session or not source_ok(source):
        items.append(missing(symbol=exchange, exchange=exchange, field="breadth", source=source, detail="Breadth needs a session date and a source."))
        return done(items, exchange=exchange, session_date=session)

    common = dict(symbol=exchange, exchange=exchange, series="BREADTH", session_date=session, as_of_ist=as_of, source=source, freshness=freshness)
    for field in ("advances", "declines", "unchanged", "new_highs", "new_lows"):
        if pack.get(field) is None:
            items.append(missing(symbol=exchange, exchange=exchange, series="BREADTH", field=field, source=source, detail="Not in the breadth file."))
        else:
            items.append(evidence(field=field, value=pack[field], unit="count", **common))

    advances = pack.get("advances")
    declines = pack.get("declines")
    if advances is not None and declines not in (None, 0):
        items.append(evidence(field="advance_decline_ratio", value=round(advances / declines, 4), unit="ratio", **common))
    else:
        items.append(
            missing(symbol=exchange, exchange=exchange, series="BREADTH", field="advance_decline_ratio", source=source, detail="Advances and a non-zero decline count are both required.")
        )

    _concentration(pack, items, common, source, exchange)
    return done(items, exchange=exchange, session_date=session)


def _concentration(pack: dict, items: list, common: dict, source: str, exchange: str) -> None:
    rows = pack.get("contributors")
    if not rows:
        items.append(
            missing(symbol=exchange, exchange=exchange, series="BREADTH", field="concentration", source=source, detail="No index contributors were supplied.")
        )
        return
    usable: list[tuple[str, float]] = []
    for row in rows:
        resolved = resolve(row.get("symbol", ""), row.get("exchange") or exchange)
        points = row.get("points")
        if not resolved["ok"] or points is None:
            items.append(
                missing(
                    symbol=row.get("symbol") or "",
                    exchange=row.get("exchange") or exchange,
                    field="contributor_points",
                    source=source,
                    detail=resolved["detail"] if not resolved["ok"] else "Contributor points were blank.",
                )
            )
            continue
        usable.append((resolved["symbol"], float(points)))
        items.append(
            evidence(
                symbol=resolved["symbol"],
                exchange=resolved["exchange"],
                series=resolved.get("series"),
                field="contributor_points",
                value=points,
                unit="index_points",
                session_date=common["session_date"],
                as_of_ist=common["as_of_ist"],
                source=source,
                freshness="previous_session",
            )
        )
    if len(usable) < 3:
        items.append(
            missing(symbol=exchange, exchange=exchange, series="BREADTH", field="concentration", source=source, detail="Need at least three index contributors.")
        )
        return
    total = sum(abs(points) for _, points in usable)
    if total == 0:
        items.append(evidence(field="concentration", value="flat", unit="label", **common))
        return
    top_symbol, top_points = max(usable, key=lambda item: abs(item[1]))
    share = abs(top_points) / total
    label = "narrow" if share >= _NARROW_SHARE else "broad"
    items.append(
        evidence(
            field="concentration",
            value=label,
            unit="label",
            detail=f"{top_symbol} share={round(share * 100, 2)} percent of absolute index points",
            **common,
        )
    )
