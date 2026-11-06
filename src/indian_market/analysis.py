"""Price, delivery, relative strength, and the futures price-OI quadrant."""

from __future__ import annotations

from typing import Any

from indian_market.evidence import evidence, missing


def _pct(new: float, old: float) -> float:
    return (new / old - 1.0) * 100.0


def _window_return(bars: list[dict[str, Any]], sessions: int) -> float | None:
    if len(bars) < sessions + 1:
        return None
    return _pct(bars[-1]["close"], bars[-(sessions + 1)]["close"])


def oi_quadrant(price_change: float, oi_change: float) -> str:
    price_up = price_change > 0
    oi_up = oi_change > 0
    if price_up and oi_up:
        return "long_buildup"
    if (not price_up) and oi_up:
        return "short_buildup"
    if (not price_up) and (not oi_up):
        return "long_unwinding"
    return "short_covering"


def analyze(pack: dict[str, Any]) -> dict[str, Any]:
    symbol = pack["symbol"]
    exchange = pack["exchange"]
    series = pack.get("series")
    source = pack.get("source") or "unspecified"
    freshness = pack.get("freshness") or "fixture"
    bars: list[dict[str, Any]] = pack.get("bars") or []
    items: list[dict[str, Any]] = []

    if len(bars) < 2:
        items.append(
            missing(
                symbol=symbol,
                exchange=exchange,
                series=series,
                field="close",
                source=source,
                detail="Need at least two daily bars.",
            )
        )
        return {"ok": False, "symbol": symbol, "exchange": exchange, "items": items}

    last, prev = bars[-1], bars[-2]
    session = last.get("date")
    as_of = pack.get("as_of_ist")
    change = _pct(last["close"], prev["close"])
    common = dict(
        symbol=symbol,
        exchange=exchange,
        series=series,
        session_date=session,
        as_of_ist=as_of,
        source=source,
        freshness=freshness,
    )
    items.append(evidence(field="close", value=last["close"], unit="INR", **common))
    items.append(evidence(field="change_pct", value=round(change, 4), unit="percent", **common))

    volume = last.get("volume")
    delivery = last.get("delivery_qty")
    if volume and delivery is not None:
        items.append(
            evidence(
                field="delivery_pct",
                value=round(delivery / volume * 100.0, 2),
                unit="percent",
                **common,
            )
        )
    else:
        items.append(
            missing(
                symbol=symbol,
                exchange=exchange,
                series=series,
                field="delivery_pct",
                source=source,
                detail="Bar has no delivery quantity. Do not estimate it.",
            )
        )

    for sessions, field in ((5, "return_5d_pct"), (20, "return_20d_pct")):
        value = _window_return(bars, sessions)
        if value is None:
            items.append(
                missing(
                    symbol=symbol,
                    exchange=exchange,
                    series=series,
                    field=field,
                    source=source,
                    detail=f"Need {sessions + 1} bars.",
                )
            )
        else:
            items.append(evidence(field=field, value=round(value, 4), unit="percent", **common))

    bench = pack.get("benchmark") or {}
    by_symbol = {bar["date"]: bar for bar in bars}
    by_bench = {bar["date"]: bar for bar in (bench.get("bars") or [])}
    common_dates = sorted(set(by_symbol) & set(by_bench))
    if len(common_dates) >= 2:
        window = common_dates[-21:]
        s_ret = _pct(by_symbol[window[-1]]["close"], by_symbol[window[0]]["close"])
        b_ret = _pct(by_bench[window[-1]]["close"], by_bench[window[0]]["close"])
        items.append(
            evidence(
                field="rs_vs_benchmark_pct",
                value=round(s_ret - b_ret, 4),
                unit="percent",
                detail=f"versus {bench.get('symbol', 'benchmark')} over {len(window) - 1} sessions",
                **common,
            )
        )
    else:
        items.append(
            missing(
                symbol=symbol,
                exchange=exchange,
                series=series,
                field="rs_vs_benchmark_pct",
                source=source,
                detail="No overlapping benchmark bars.",
            )
        )

    futures = pack.get("futures")
    if futures and None not in (
        futures.get("close"),
        futures.get("prev_close"),
        futures.get("oi"),
        futures.get("prev_oi"),
    ):
        price_chg = futures["close"] - futures["prev_close"]
        oi_chg = futures["oi"] - futures["prev_oi"]
        if price_chg == 0 or oi_chg == 0:
            quadrant = "flat"
        else:
            quadrant = oi_quadrant(price_chg, oi_chg)
        items.append(
            evidence(
                field="fut_oi_quadrant",
                value=quadrant,
                unit="label",
                detail=f"price_change={round(price_chg, 4)}, oi_change={round(oi_chg, 4)}",
                **common,
            )
        )
    else:
        items.append(
            missing(
                symbol=symbol,
                exchange=exchange,
                series=series,
                field="fut_oi_quadrant",
                source=source,
                detail="No futures close and open interest for this name.",
            )
        )

    usable = any(item["ok"] for item in items)
    return {"ok": usable, "symbol": symbol, "exchange": exchange, "series": series, "items": items}
