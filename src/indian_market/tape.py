"""Session tape from minute bars. This is not an exchange time-and-sales feed."""

from __future__ import annotations

from typing import Any

from indian_market.evidence import evidence, missing


def _hhmm(value: str) -> tuple[int, int]:
    hour, minute = value.split(":")
    return int(hour), int(minute)


def _in_opening_range(stamp: str) -> bool:
    hour, minute = _hhmm(stamp)
    minutes = hour * 60 + minute
    return 9 * 60 + 15 <= minutes < 9 * 60 + 30


def read_tape(pack: dict[str, Any]) -> dict[str, Any]:
    symbol = pack["symbol"]
    exchange = pack["exchange"]
    series = pack.get("series")
    mode = pack.get("mode") or "session"
    source = pack.get("source") or "unspecified"
    freshness = pack.get("freshness") or "fixture"
    common = dict(
        symbol=symbol,
        exchange=exchange,
        series=series,
        session_date=pack.get("session_date"),
        as_of_ist=pack.get("as_of_ist"),
        source=source,
        freshness=freshness,
    )
    items: list[dict[str, Any]] = [
        evidence(field="tape_mode", value=mode, unit="label", **common)
    ]

    if mode == "prints":
        prints = pack.get("prints") or []
        if not prints:
            items.append(
                missing(
                    symbol=symbol,
                    exchange=exchange,
                    series=series,
                    field="prints",
                    source=source,
                    detail="Print mode needs a broker or vendor time-and-sales feed. None was supplied.",
                )
            )
            return _done(symbol, exchange, series, mode, items)
        sizes = [row["qty"] for row in prints]
        average = sum(sizes) / len(sizes)
        large = [row for row in prints if row["qty"] >= average * 5]
        items.append(evidence(field="print_count", value=len(prints), unit="trades", **common))
        items.append(
            evidence(field="large_print_count", value=len(large), unit="trades", detail="qty >= 5x average print", **common)
        )
        return _done(symbol, exchange, series, mode, items)

    for field, key in (("prev_high", "prev_high"), ("prev_low", "prev_low"), ("prev_close", "prev_close")):
        if pack.get(key) is None:
            items.append(
                missing(symbol=symbol, exchange=exchange, series=series, field=field, source=source, detail="Not in the pack.")
            )
        else:
            items.append(evidence(field=field, value=pack[key], unit="INR", **common))

    if pack.get("delivery_pct") is None:
        items.append(
            missing(
                symbol=symbol,
                exchange=exchange,
                series=series,
                field="delivery_pct",
                source=source,
                detail="Delivery percent is published after the close. Do not estimate it.",
            )
        )
    else:
        items.append(
            evidence(
                field="delivery_pct",
                value=pack["delivery_pct"],
                unit="percent",
                session_date=pack.get("delivery_session") or pack.get("session_date"),
                as_of_ist=pack.get("as_of_ist"),
                source=source,
                freshness="previous_session" if pack.get("delivery_session") else freshness,
                symbol=symbol,
                exchange=exchange,
                series=series,
                detail="From the cash bhavcopy. During the session this is the previous close.",
            )
        )

    bars = pack.get("bars_1m") or []
    if not bars:
        items.append(
            missing(
                symbol=symbol,
                exchange=exchange,
                series=series,
                field="vwap",
                source=source,
                detail="No minute bars. VWAP and the opening range stay blank.",
            )
        )
        items.append(
            missing(
                symbol=symbol,
                exchange=exchange,
                series=series,
                field="opening_range",
                source=source,
                detail="No minute bars.",
            )
        )
    else:
        turned = 0.0
        volume = 0.0
        for bar in bars:
            typical = (bar["h"] + bar["l"] + bar["c"]) / 3.0
            turned += typical * bar["v"]
            volume += bar["v"]
        vwap = turned / volume if volume else None
        items.append(
            evidence(
                field="vwap",
                value=None if vwap is None else round(vwap, 4),
                unit="INR",
                detail="typical price (H+L+C)/3 times volume, on the bars supplied",
                **common,
            )
        )
        opening = [bar for bar in bars if _in_opening_range(bar["t"])]
        if opening:
            items.append(
                evidence(
                    field="opening_range_high",
                    value=max(bar["h"] for bar in opening),
                    unit="INR",
                    detail="09:15 inclusive to 09:30 exclusive IST",
                    **common,
                )
            )
            items.append(
                evidence(
                    field="opening_range_low",
                    value=min(bar["l"] for bar in opening),
                    unit="INR",
                    detail="09:15 inclusive to 09:30 exclusive IST",
                    **common,
                )
            )
        else:
            items.append(
                missing(
                    symbol=symbol,
                    exchange=exchange,
                    series=series,
                    field="opening_range",
                    source=source,
                    detail="Minute bars do not cover 09:15–09:30 IST.",
                )
            )
        last = bars[-1]["c"]
        if vwap is not None:
            location = "above" if last > vwap else "below" if last < vwap else "at"
            items.append(evidence(field="last_vs_vwap", value=location, unit="label", **common))

    return _done(symbol, exchange, series, mode, items)


def _done(symbol: str, exchange: str, series: str | None, mode: str, items: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "ok": any(item["ok"] for item in items),
        "symbol": symbol,
        "exchange": exchange,
        "series": series,
        "mode": mode,
        "items": items,
    }
