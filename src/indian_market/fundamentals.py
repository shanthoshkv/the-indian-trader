"""Quarterly and annual lines. The fiscal year runs April to March.

Ratios are computed only from numbers in the pack. A mismatched period label
drops that row instead of being relabeled in silence.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from indian_market.evidence import evidence, missing
from indian_market.records import as_date, done, freshness_for, source_ok


def fiscal_year(day: date) -> str:
    year = day.year + 1 if day.month >= 4 else day.year
    return f"FY{year}"


def quarter_label(day: date) -> str:
    if 4 <= day.month <= 6:
        quarter = "Q1"
    elif day.month <= 9:
        quarter = "Q2"
    elif day.month <= 12:
        quarter = "Q3"
    else:
        quarter = "Q4"
    return f"{quarter} {fiscal_year(day)}"


def _stated_matches(stated: str | None, computed: str) -> bool:
    if not stated:
        return True
    left = stated.upper().replace(" ", "")
    right = computed.upper().replace(" ", "")
    short = right.replace("FY20", "FY")
    return left in {right, short}


def read_fundamentals(pack: dict[str, Any]) -> dict[str, Any]:
    symbol = pack["symbol"]
    exchange = pack["exchange"]
    series = pack.get("series")
    source = pack.get("source") or "unspecified"
    as_of = pack.get("as_of_ist")
    items: list[dict[str, Any]] = []
    if not source_ok(source):
        items.append(missing(symbol=symbol, exchange=exchange, series=series, field="fundamentals", source=source, detail="Fundamentals need an NSE, BSE, http, or fixture source."))
        return done(items, symbol=symbol, exchange=exchange, series=series)

    latest_eps: tuple[str, float] | None = None
    for row in pack.get("quarters") or []:
        eps = _statement(row, items, symbol, exchange, series, source, as_of, annual=False)
        if eps is not None:
            latest_eps = eps
    for row in pack.get("annual") or []:
        _statement(row, items, symbol, exchange, series, source, as_of, annual=True)

    _price_and_pe(pack, items, symbol, exchange, series, source, as_of, latest_eps)
    _pledge(pack, items, symbol, exchange, series, source, as_of)
    _holders(pack, items, symbol, exchange, series, source, as_of)
    if not items:
        items.append(missing(symbol=symbol, exchange=exchange, series=series, field="fundamentals", source=source, detail="No statement, pledge, or shareholding rows were in the pack."))
    return done(items, symbol=symbol, exchange=exchange, series=series)


def _statement(row, items, symbol, exchange, series, source, as_of, *, annual: bool) -> tuple[str, float] | None:
    if not row.get("period_end"):
        items.append(missing(symbol=symbol, exchange=exchange, series=series, field="period", source=source, detail="A statement needs period_end."))
        return None
    day = as_date(row["period_end"])
    if annual and (day.month, day.day) != (3, 31):
        items.append(
            missing(symbol=symbol, exchange=exchange, series=series, field="annual", source=source, detail=f"{row['period_end']} is not 31 March. The Indian fiscal year ends that day.")
        )
        return None
    label = fiscal_year(day) if annual else quarter_label(day)
    stated = row.get("period") or row.get("fiscal_year")
    if not _stated_matches(stated if annual else row.get("period"), label):
        items.append(
            missing(
                symbol=symbol,
                exchange=exchange,
                series=series,
                field="period",
                source=source,
                detail=f"period_end {row['period_end']} is {label}, not {stated}.",
            )
        )
        return None
    if annual and row.get("fiscal_year") and not _stated_matches(row["fiscal_year"], fiscal_year(day)):
        items.append(
            missing(symbol=symbol, exchange=exchange, series=series, field="period", source=source, detail=f"period_end {row['period_end']} is {fiscal_year(day)}, not {row['fiscal_year']}.")
        )
        return None
    common = dict(
        symbol=symbol,
        exchange=exchange,
        series=series,
        session_date=row["period_end"],
        as_of_ist=as_of,
        source=row.get("source") or source,
        freshness=freshness_for(row.get("source") or source, "filing"),
        detail=label,
    )
    eps_value = None
    for field in ("sales", "pat", "eps", "equity", "debt"):
        if row.get(field) is None:
            continue
        items.append(evidence(field=field, value=row[field], unit="INR", **common))
        if field == "eps":
            eps_value = (row["period_end"], float(row[field]))
    if row.get("sales") not in (None, 0) and row.get("pat") is not None:
        items.append(evidence(field="pat_margin_pct", value=round(row["pat"] / row["sales"] * 100.0, 4), unit="percent", **common))
    if annual and row.get("equity") not in (None, 0) and row.get("pat") is not None:
        items.append(evidence(field="roe_pct", value=round(row["pat"] / row["equity"] * 100.0, 4), unit="percent", **common))
    return eps_value


def _price_and_pe(pack, items, symbol, exchange, series, source, as_of, latest_eps) -> None:
    price = pack.get("price") or {}
    if price.get("value") is None or not price.get("session_date"):
        items.append(missing(symbol=symbol, exchange=exchange, series=series, field="pe", source=source, detail="No price with a session date. Do not use a remembered price."))
        return
    items.append(
        evidence(
            symbol=symbol,
            exchange=exchange,
            series=series,
            field="price",
            value=price["value"],
            unit="INR",
            session_date=price["session_date"],
            as_of_ist=as_of,
            source=price.get("source") or source,
            freshness=freshness_for(price.get("source") or source, "previous_session"),
        )
    )
    if latest_eps is None or latest_eps[1] == 0:
        items.append(missing(symbol=symbol, exchange=exchange, series=series, field="pe", source=source, detail="No quarterly earnings per share in the pack."))
        return
    items.append(
        evidence(
            symbol=symbol,
            exchange=exchange,
            series=series,
            field="pe",
            value=round(price["value"] / latest_eps[1], 4),
            unit="ratio",
            session_date=price["session_date"],
            as_of_ist=as_of,
            source=source,
            freshness=freshness_for(source, "filing"),
            detail=f"price / quarterly eps for period_end {latest_eps[0]}",
        )
    )


def _pledge(pack, items, symbol, exchange, series, source, as_of) -> None:
    row = pack.get("pledge")
    if not row or row.get("pct") is None:
        items.append(missing(symbol=symbol, exchange=exchange, series=series, field="pledge_pct", source=source, detail="No promoter pledge figure was in the pack."))
        return
    items.append(
        evidence(
            symbol=symbol,
            exchange=exchange,
            series=series,
            field="pledge_pct",
            value=row["pct"],
            unit="percent",
            session_date=row.get("as_of"),
            as_of_ist=as_of,
            source=row.get("source") or source,
            freshness=freshness_for(row.get("source") or source, "filing"),
            detail="Promoter shares pledged.",
        )
    )


def _holders(pack, items, symbol, exchange, series, source, as_of) -> None:
    rows = pack.get("shareholding") or []
    if not rows:
        items.append(missing(symbol=symbol, exchange=exchange, series=series, field="holding_pct", source=source, detail="No shareholding rows were in the pack."))
        return
    total = 0.0
    counted = 0
    for row in rows:
        if row.get("holder") is None or row.get("pct") is None:
            items.append(missing(symbol=symbol, exchange=exchange, series=series, field="holding_pct", source=source, detail="A shareholding row needs a holder and a percent."))
            continue
        items.append(
            evidence(
                symbol=symbol,
                exchange=exchange,
                series=series,
                field="holding_pct",
                value=row["pct"],
                unit="percent",
                session_date=row.get("as_of"),
                as_of_ist=as_of,
                source=row.get("source") or source,
                freshness=freshness_for(row.get("source") or source, "filing"),
                detail=str(row["holder"]),
            )
        )
        total += float(row["pct"])
        counted += 1
    if counted:
        items.append(
            evidence(
                symbol=symbol,
                exchange=exchange,
                series=series,
                field="shareholding_sum_pct",
                value=round(total, 4),
                unit="percent",
                session_date=rows[0].get("as_of"),
                as_of_ist=as_of,
                source=source,
                freshness=freshness_for(source, "filing"),
                detail="Sum of the holding rows supplied. A partial table will not equal 100.",
            )
        )
