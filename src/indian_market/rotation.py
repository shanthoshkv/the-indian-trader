"""Sector index return minus Nifty or Sensex over 5, 20, and 60 sessions."""

from __future__ import annotations

from typing import Any

from indian_market.evidence import evidence, missing
from indian_market.records import done, source_ok
from indian_market.universe import resolve

_WINDOWS = (5, 20, 60)


def _pct(new: float, old: float) -> float:
    return (new / old - 1.0) * 100.0


def _relative(sector_bars: list[dict], bench_bars: list[dict], sessions: int) -> float | None:
    sector = {bar["date"]: bar["close"] for bar in sector_bars}
    bench = {bar["date"]: bar["close"] for bar in bench_bars}
    common = sorted(set(sector) & set(bench))
    if len(common) < sessions + 1:
        return None
    window = common[-(sessions + 1) :]
    sector_return = _pct(sector[window[-1]], sector[window[0]])
    bench_return = _pct(bench[window[-1]], bench[window[0]])
    return sector_return - bench_return


def read_rotation(pack: dict[str, Any]) -> dict[str, Any]:
    source = pack.get("source") or "unspecified"
    session = pack.get("session_date")
    as_of = pack.get("as_of_ist")
    freshness = pack.get("freshness") or "previous_session"
    bench_row = pack.get("benchmark") or {}
    bench = resolve(bench_row.get("symbol", ""), bench_row.get("exchange"))
    if not bench["ok"]:
        return {"ok": False, "error": "outside_universe", "detail": bench["detail"]}
    if bench["symbol"] not in {"NIFTY", "SENSEX"}:
        return {
            "ok": False,
            "error": "outside_universe",
            "detail": "The benchmark is Nifty or Sensex.",
        }
    items: list[dict[str, Any]] = []
    if not source_ok(source):
        items.append(missing(symbol=bench["symbol"], exchange=bench["exchange"], field="sector_rs", source=source, detail="Sector bars need a source."))
        return done(items)
    bench_bars = bench_row.get("bars") or []
    for row in pack.get("sectors") or []:
        resolved = resolve(row.get("symbol", ""), row.get("exchange"))
        if not resolved["ok"]:
            items.append(missing(symbol=row.get("symbol") or "", exchange=row.get("exchange") or "", field="sector_rs", source=source, detail=resolved["detail"]))
            continue
        for sessions in _WINDOWS:
            field = f"rs_{sessions}d_pct"
            value = _relative(row.get("bars") or [], bench_bars, sessions)
            if value is None:
                items.append(
                    missing(
                        symbol=resolved["symbol"],
                        exchange=resolved["exchange"],
                        series=resolved.get("series"),
                        field=field,
                        source=source,
                        detail=f"Need {sessions + 1} dates in common with {bench['symbol']}.",
                    )
                )
                continue
            items.append(
                evidence(
                    symbol=resolved["symbol"],
                    exchange=resolved["exchange"],
                    series=resolved.get("series"),
                    field=field,
                    value=round(value, 4),
                    unit="percent",
                    session_date=session,
                    as_of_ist=as_of,
                    source=source,
                    freshness=freshness if not source.startswith("fixture:") else "fixture",
                    detail=f"versus {bench['symbol']} over {sessions} sessions",
                )
            )
    if not pack.get("sectors"):
        items.append(missing(symbol=bench["symbol"], exchange=bench["exchange"], series="INDEX", field="sector_rs", source=source, detail="No sector indexes were in the pack."))
    return done(items, benchmark=bench["symbol"], session_date=session)
