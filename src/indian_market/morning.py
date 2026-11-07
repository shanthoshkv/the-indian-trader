"""One morning chain. It calls the other commands. It does not invent a number.

BLOCK stops the chain before a ticket. Nothing is sent to a broker.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from indian_market.evidence import evidence, missing
from indian_market.gate import assess_gate
from indian_market.journal import open_risk_inr
from indian_market.paths import data_dir
from indian_market.premarket import build_premarket
from indian_market.records import done, source_ok
from indian_market.scanner import scan_list
from indian_market.sizing import size_position
from indian_market.strategies import SETUPS
from indian_market.surveillance import clear
from indian_market.ticket import build_ticket


def load_watchlist() -> dict[str, Any]:
    return json.loads((data_dir() / "watchlist.json").read_text(encoding="utf-8"))


def run_morning(pack: dict[str, Any]) -> dict[str, Any]:
    source = pack.get("source") or "unspecified"
    session = pack.get("session_date")
    symbol = (pack.get("setup_pack") or {}).get("symbol") or pack.get("symbol") or "NSE"
    exchange = (pack.get("setup_pack") or {}).get("exchange") or pack.get("exchange") or "NSE"
    items: list[dict[str, Any]] = []
    if not session or not source_ok(source):
        items.append(missing(symbol=symbol, exchange=exchange, field="morning", source=source, detail="The morning chain needs a session date and a source."))
        return done(items, chain_status="incomplete")

    if pack.get("premarket"):
        items.extend(build_premarket(pack["premarket"]).get("items") or [])
    else:
        items.append(missing(symbol=symbol, exchange=exchange, field="premarket", source=source, detail="No premarket pack was supplied."))

    facts = pack.get("surveillance") or {}
    if not facts.get("symbol"):
        items.append(missing(symbol=symbol, exchange=exchange, field="surveillance", source=source, detail="Surveillance facts are required before a setup."))
        return done(items, symbol=symbol, exchange=exchange, chain_status="incomplete")
    cleared = clear(facts, segment=pack.get("segment") or "cash")
    items.append(_label(symbol, exchange, facts.get("series"), "clearance", cleared["clearance"], session, source, "From surveillance-check."))

    scan_pack = dict(pack.get("scan") or {})
    if pack.get("use_watchlist"):
        allowed = {row["symbol"] for row in load_watchlist().get("names") or []}
        kept = []
        for row in scan_pack.get("names") or []:
            if row.get("symbol") in allowed:
                kept.append(row)
            else:
                items.append(missing(symbol=row.get("symbol") or "", exchange=row.get("exchange") or "NSE", field="scan_hit", source=source, detail="Not on the watchlist."))
        scan_pack["names"] = kept
        scan_pack.setdefault("source", source)
        scan_pack.setdefault("session_date", session)
    if scan_pack.get("names"):
        items.extend(scan_list(scan_pack).get("items") or [])

    setup_name = pack.get("setup") or "orb"
    runner = SETUPS.get(setup_name)
    setup_pack = dict(pack.get("setup_pack") or {})
    if runner is None:
        items.append(missing(symbol=symbol, exchange=exchange, field="setup", source=source, detail="Setup is orb, pdh, vwap, delivery, sector, or post."))
        return done(items, chain_status="incomplete")
    setup_pack.setdefault("source", source)
    setup_pack.setdefault("session_date", session)
    setup_pack["surveillance"] = {
        "clearance": cleared["clearance"],
        "source": facts.get("source") or source,
        "session_date": facts.get("session_date") or session,
    }
    if facts.get("trade_for_trade"):
        setup_pack["trade_for_trade"] = True
    planned = runner(setup_pack)
    items.extend(planned.get("items") or [])
    if planned.get("plan_status") != "ready":
        items.append(missing(symbol=symbol, exchange=exchange, field="ticket", source=source, detail="The setup is not ready. No ticket."))
        return done(items, symbol=symbol, exchange=exchange, chain_status=planned.get("plan_status") or "incomplete", plan_status=planned.get("plan_status"))

    size_pack = dict(pack.get("size") or {})
    size_pack.setdefault("symbol", setup_pack.get("symbol"))
    size_pack.setdefault("exchange", setup_pack.get("exchange"))
    size_pack.setdefault("series", setup_pack.get("series"))
    size_pack.setdefault("source", source)
    size_pack.setdefault("session_date", session)
    size_pack["plan_status"] = "ready"
    size_pack["horizon"] = _value(planned, "horizon")
    size_pack["entry"] = _value(planned, "entry")
    size_pack["invalidation"] = _value(planned, "invalidation")
    size_pack["clearance"] = cleared["clearance"]
    sized = size_position(size_pack)
    items.extend(sized.get("items") or [])

    gate_pack = dict(pack.get("gate") or {})
    gate_pack.setdefault("symbol", setup_pack.get("symbol"))
    gate_pack.setdefault("exchange", setup_pack.get("exchange"))
    gate_pack.setdefault("source", source)
    gate_pack.setdefault("session_date", session)
    gate_pack.setdefault("horizon", size_pack["horizon"])
    gate_pack.setdefault("clearance", cleared["clearance"])
    gate_pack.setdefault("r_multiple", _value(planned, "r_multiple"))
    if pack.get("journal_path"):
        gate_pack["open_risk_inr"] = open_risk_inr(Path(pack["journal_path"]))
    if planned.get("muhurat"):
        gate_pack["muhurat"] = True
    decision = assess_gate(gate_pack)
    items.extend(decision.get("items") or [])
    if decision.get("gate") != "PASS":
        items.append(missing(symbol=symbol, exchange=exchange, field="ticket", source=source, detail="BLOCK stops the chain. No ticket."))
        return done(items, symbol=symbol, exchange=exchange, chain_status="BLOCK", gate="BLOCK")

    ticket_pack = pack.get("ticket")
    if not ticket_pack:
        items.append(_label(symbol, exchange, None, "chain", "gate_pass", session, source, "No ticket was requested. Nothing was sent to a broker."))
        return done(items, symbol=symbol, exchange=exchange, chain_status="gate_pass", gate="PASS")
    built = dict(ticket_pack)
    built.setdefault("symbol", setup_pack.get("symbol"))
    built.setdefault("exchange", setup_pack.get("exchange"))
    built.setdefault("source", source)
    built.setdefault("session_date", session)
    built["gate"] = "PASS"
    built.setdefault("quantity", _value(sized, "quantity"))
    built.setdefault("horizon", size_pack["horizon"])
    ticket = build_ticket(built)
    items.extend(ticket.get("items") or [])
    return done(items, symbol=symbol, exchange=exchange, chain_status=ticket.get("ticket_status"), gate="PASS")


def _value(payload: dict[str, Any], field: str):
    for item in payload.get("items") or []:
        if item.get("field") == field and item.get("ok"):
            return item.get("value")
    return None


def _label(symbol, exchange, series, field, value, session, source, detail):
    return evidence(
        symbol=symbol,
        exchange=exchange,
        series=series,
        field=field,
        value=value,
        unit="label",
        session_date=session,
        as_of_ist=None,
        source=source,
        freshness="fixture" if str(source).startswith("fixture:") else "previous_session",
        detail=detail,
    )
