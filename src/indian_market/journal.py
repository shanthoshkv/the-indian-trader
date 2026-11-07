"""Append-only local journal. Lines are added. Earlier lines are not rewritten."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from indian_market.calendar_in import IST
from indian_market.costs import charge_rate
from indian_market.evidence import evidence, missing
from indian_market.records import as_date, as_ist, done, source_ok
from indian_market.universe import resolve

_CLOSED = {"target_hit", "stopped", "scratched"}
_STT = {
    "intraday_cash": ("stt_equity_intraday_sell",),
    "delivery": ("stt_equity_delivery_buy", "stt_equity_delivery_sell"),
    "futures": ("stt_fut_sell",),
    "options": ("stt_opt_premium_sell",),
}

_OUTCOMES = {"target_hit", "stopped", "open", "scratched"}


def logged_at(value: str | None) -> str:
    if not value:
        return datetime.now(IST).isoformat()
    return as_ist(value).isoformat()


def append_event(path: Path, event: dict[str, Any]) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")
    return {"ok": True, "path": str(path), "event": event}


def read_events(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def reconstruct(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    plans: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for event in events:
        kind = event.get("event")
        identity = event.get("id")
        if kind == "plan" and identity:
            plans[identity] = dict(event)
            order.append(identity)
        elif kind == "outcome" and identity in plans:
            plans[identity]["outcome"] = event.get("outcome")
            plans[identity]["outcome_at_ist"] = event.get("logged_at_ist")
            if event.get("realized_r") is not None:
                plans[identity]["realized_r"] = event["realized_r"]
            if event.get("exit_price") is not None:
                plans[identity]["exit_price"] = event["exit_price"]
        elif kind == "human_yes" and identity in plans:
            plans[identity]["human_yes"] = True
            plans[identity]["human_yes_at_ist"] = event.get("logged_at_ist")
    return [plans[identity] for identity in order]


def show_journal(path: Path) -> dict[str, Any]:
    events = read_events(path)
    return {"ok": True, "path": str(path), "lines": len(events), "entries": reconstruct(events)}


def add_plan(path: Path, pack: dict[str, Any], at: str | None = None) -> dict[str, Any]:
    resolved = resolve(pack.get("symbol", ""), pack.get("exchange"))
    if not resolved["ok"]:
        return resolved
    if not pack.get("setup") or pack.get("planned_risk_inr") is None or not source_ok(pack.get("source")):
        return {"ok": False, "error": "bad_input", "detail": "A journal plan needs a setup, planned risk in rupees, and a source."}
    stamp = logged_at(at or pack.get("as_of_ist"))
    event = {
        "event": "plan",
        "id": pack.get("id") or f"{resolved['symbol']}-{stamp}",
        "logged_at_ist": stamp,
        "symbol": resolved["symbol"],
        "exchange": resolved["exchange"],
        "series": resolved.get("series"),
        "setup": pack["setup"],
        "horizon": pack.get("horizon"),
        "planned_risk_inr": pack["planned_risk_inr"],
        "source": pack["source"],
        "outcome": None,
    }
    for key in ("entry", "qty", "side"):
        if pack.get(key) is not None:
            event[key] = pack[key]
    written = append_event(path, event)
    written["entries"] = reconstruct(read_events(path))
    return written


def add_outcome(
    path: Path,
    identity: str,
    outcome: str,
    at: str | None = None,
    source: str | None = None,
    realized_r: float | None = None,
    exit_price: float | None = None,
) -> dict[str, Any]:
    if outcome not in _OUTCOMES:
        return {"ok": False, "error": "bad_input", "detail": "Outcome is target_hit, stopped, open, or scratched."}
    known = {row.get("id") for row in read_events(path) if row.get("event") == "plan"}
    if identity not in known:
        return {"ok": False, "error": "unknown_id", "detail": "That plan id is not in the journal. Nothing was written."}
    event = {
        "event": "outcome",
        "id": identity,
        "outcome": outcome,
        "logged_at_ist": logged_at(at),
        "source": source or "journal",
    }
    if realized_r is not None:
        event["realized_r"] = realized_r
    if exit_price is not None:
        event["exit_price"] = exit_price
    written = append_event(path, event)
    written["entries"] = reconstruct(read_events(path))
    return written


def add_human_yes(path: Path, pack: dict[str, Any], at: str | None = None) -> dict[str, Any]:
    identity = pack.get("id")
    if not identity:
        return {"ok": False, "error": "bad_input", "detail": "A human yes needs the plan id."}
    known = {row.get("id") for row in read_events(path) if row.get("event") == "plan"}
    if identity not in known:
        return {"ok": False, "error": "unknown_id", "detail": "That plan id is not in the journal. The yes was not stored."}
    event = {
        "event": "human_yes",
        "id": identity,
        "logged_at_ist": logged_at(at or pack.get("as_of_ist")),
        "ticket": pack.get("ticket"),
        "source": pack.get("source") or "journal",
    }
    written = append_event(path, event)
    written["entries"] = reconstruct(read_events(path))
    return written


def open_risk_inr(path: Path) -> float:
    total = 0.0
    for row in reconstruct(read_events(path)):
        if row.get("outcome") in (None, "open"):
            total += float(row.get("planned_risk_inr") or 0)
    return total


def review_journal(path: Path, as_of: str | None = None) -> dict[str, Any]:
    """Hit rate, average realized R, and net after STT. Open rows stay out of the hit rate."""
    rows = reconstruct(read_events(path))
    items: list[dict[str, Any]] = []
    source = "data/costs.json"
    groups: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        groups.setdefault(row.get("setup") or "unnamed", []).append(row)
    closed = [row for row in rows if row.get("outcome") in _CLOSED]
    hits = [row for row in closed if row.get("outcome") == "target_hit"]
    if not closed:
        items.append(missing(symbol="NSE", exchange="NSE", field="hit_rate", source=source, detail="No closed outcome is in the journal."))
    else:
        items.append(
            evidence(
                symbol="NSE",
                exchange="NSE",
                field="hit_rate",
                value=round(len(hits) / len(closed), 4),
                unit="ratio",
                session_date=as_of,
                as_of_ist=None,
                source=source,
                freshness="filing",
                detail=f"{len(hits)} target_hit of {len(closed)} closed. Open rows are excluded.",
            )
        )
    rated = [row for row in closed if row.get("realized_r") is not None]
    if not rated:
        items.append(missing(symbol="NSE", exchange="NSE", field="avg_r", source=source, detail="No closed row has a realized R."))
    else:
        average = sum(float(row["realized_r"]) for row in rated) / len(rated)
        items.append(
            evidence(
                symbol="NSE",
                exchange="NSE",
                field="avg_r",
                value=round(average, 4),
                unit="ratio",
                session_date=as_of,
                as_of_ist=None,
                source=source,
                freshness="filing",
                detail=f"{len(rated)} closed rows with a realized R.",
            )
        )
    total_net = 0.0
    net_ok = True
    counted = 0
    for setup, members in groups.items():
        _group(items, setup, members, source, as_of)
    for row in closed:
        scored = _net(row)
        if not scored["ok"]:
            net_ok = False
            items.append(missing(symbol=row.get("symbol") or "NSE", exchange=row.get("exchange") or "NSE", field="trade_net_inr", source=source, detail=scored["detail"]))
            continue
        counted += 1
        total_net += scored["net"]
        items.append(
            evidence(
                symbol=row.get("symbol") or "NSE",
                exchange=row.get("exchange") or "NSE",
                series=row.get("series"),
                field="trade_net_inr",
                value=round(scored["net"], 2),
                unit="INR",
                session_date=scored["session"],
                as_of_ist=None,
                source=source,
                freshness="filing",
                detail=row.get("id"),
            )
        )
    if counted and net_ok:
        items.append(
            evidence(
                symbol="NSE",
                exchange="NSE",
                field="net_after_stt_inr",
                value=round(total_net, 2),
                unit="INR",
                session_date=as_of,
                as_of_ist=None,
                source=source,
                freshness="filing",
                detail="Gross price result minus STT. Exchange transaction charges are not in this net.",
            )
        )
    else:
        items.append(missing(symbol="NSE", exchange="NSE", field="net_after_stt_inr", source=source, detail="A closed row is missing entry, exit, quantity, or a usable STT rate."))
    items.append(
        evidence(
            symbol="NSE",
            exchange="NSE",
            field="open_risk_inr",
            value=round(open_risk_inr(path), 2),
            unit="INR",
            session_date=as_of,
            as_of_ist=None,
            source="NSE journal",
            freshness="filing",
            detail="Sum of planned risk on rows that are still open.",
        )
    )
    return done(items, path=str(path), lines=len(read_events(path)))


def _group(items, setup, members, source, as_of) -> None:
    closed = [row for row in members if row.get("outcome") in _CLOSED]
    if not closed:
        return
    hits = sum(1 for row in closed if row.get("outcome") == "target_hit")
    items.append(evidence(symbol="NSE", exchange="NSE", field="setup_hit_rate", value=round(hits / len(closed), 4), unit="ratio", session_date=as_of, as_of_ist=None, source=source, freshness="filing", detail=setup))
    rated = [row for row in closed if row.get("realized_r") is not None]
    if rated:
        average = sum(float(row["realized_r"]) for row in rated) / len(rated)
        items.append(evidence(symbol="NSE", exchange="NSE", field="setup_avg_r", value=round(average, 4), unit="ratio", session_date=as_of, as_of_ist=None, source=source, freshness="filing", detail=setup))


def _net(row: dict[str, Any]) -> dict[str, Any]:
    if None in (row.get("entry"), row.get("exit_price"), row.get("qty")) or row.get("horizon") not in _STT:
        return {"ok": False, "detail": "A closed review row needs entry, exit price, quantity, and a horizon."}
    side = row.get("side") or "long"
    entry, exit_, qty = float(row["entry"]), float(row["exit_price"]), float(row["qty"])
    gross = (exit_ - entry) * qty if side == "long" else (entry - exit_) * qty
    on = as_date(row.get("outcome_at_ist") or "2026-11-06")
    rates = []
    for item_id in _STT[row["horizon"]]:
        found = charge_rate(item_id, on)
        if not found["ok"]:
            return found
        rates.append(found["rate"])
    if row["horizon"] == "delivery":
        buy = entry if side == "long" else exit_
        sell = exit_ if side == "long" else entry
        stt = abs(buy) * qty * rates[0] + abs(sell) * qty * rates[1]
    else:
        sell = exit_ if side == "long" else entry
        stt = abs(sell) * qty * rates[0]
    return {"ok": True, "net": gross - stt, "session": on.isoformat()}
