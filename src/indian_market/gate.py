"""PASS or BLOCK. BLOCK is a finished answer and stops the chain."""

from __future__ import annotations

from typing import Any

from indian_market.costs import review_status
from indian_market.evidence import evidence
from indian_market.plan import HORIZONS
from indian_market.records import as_date, as_ist, done, source_ok


def assess_gate(pack: dict[str, Any]) -> dict[str, Any]:
    symbol = pack.get("symbol") or "NSE"
    exchange = pack.get("exchange") or "NSE"
    series = pack.get("series")
    source = pack.get("source") or "unspecified"
    session = pack.get("session_date")
    reasons: list[str] = []
    if not source_ok(source):
        reasons.append("No source on the gate pack.")
    if pack.get("horizon") not in HORIZONS:
        reasons.append("Horizon is missing or not an Indian product.")
    clearance = pack.get("clearance")
    if clearance == "blocked":
        reasons.append("Surveillance clearance is blocked.")
    elif clearance not in {"clear", "caution"}:
        reasons.append("Surveillance clearance is missing.")
    if pack.get("fo_ban") and pack.get("horizon") in {"futures", "options"}:
        reasons.append("The name is in F&O ban.")
    if pack.get("trade_for_trade") and pack.get("horizon") == "intraday_cash":
        reasons.append("Trade for trade cannot be an intraday cash plan.")
    if pack.get("near_circuit"):
        reasons.append("Price is near the circuit.")
    if pack.get("results_day"):
        reasons.append("The session is a results day for this name.")
    if pack.get("expiry_day") and pack.get("horizon") in {"futures", "options"}:
        reasons.append("This contract expires in the session.")
    _risk_reward(pack, reasons)
    _loss_and_count(pack, reasons)
    _session_flags(pack, reasons)
    _fresh(pack, reasons)
    _costs(pack, reasons)
    gate = "BLOCK" if reasons else "PASS"
    items = [
        evidence(
            symbol=symbol,
            exchange=exchange,
            series=series,
            field="gate",
            value=gate,
            unit="label",
            session_date=session,
            as_of_ist=pack.get("now_ist"),
            source=source,
            freshness="fixture" if str(source).startswith("fixture:") else "live_snapshot",
            detail="; ".join(reasons) if reasons else "Every supplied check passed.",
        )
    ]
    return done(items, symbol=symbol, exchange=exchange, series=series, gate=gate, reasons=reasons)


def _risk_reward(pack: dict, reasons: list[str]) -> None:
    multiple = pack.get("r_multiple")
    minimum = pack.get("min_r")
    if multiple is None or minimum is None:
        reasons.append("Reward to risk and the minimum R are both required.")
        return
    if multiple < minimum:
        reasons.append(f"R multiple {multiple} is below the minimum {minimum}.")


def _loss_and_count(pack: dict, reasons: list[str]) -> None:
    loss, limit = pack.get("daily_loss_inr"), pack.get("daily_loss_limit_inr")
    if loss is None or limit is None:
        reasons.append("Daily loss and the daily loss limit are both required.")
    elif loss >= limit:
        reasons.append("Daily loss has reached the limit.")
    planned, cap = pack.get("planned_trades"), pack.get("max_planned_trades")
    if planned is None or cap is None:
        reasons.append("The count of trades already planned and the cap are both required.")
    elif planned >= cap:
        reasons.append("The plan cap for this session is already used.")


def _fresh(pack: dict, reasons: list[str]) -> None:
    stamped = pack.get("data_as_of_ist")
    now = pack.get("now_ist")
    minutes = pack.get("max_age_minutes")
    if not stamped or not now or minutes is None:
        reasons.append("No timestamp, so freshness cannot be checked.")
        return
    age = (as_ist(now) - as_ist(stamped)).total_seconds() / 60.0
    if age < 0 or age > minutes:
        reasons.append(f"Evidence is {round(age, 1)} minutes from the decision clock. The cap is {minutes}.")


def _session_flags(pack: dict, reasons: list[str]) -> None:
    if pack.get("muhurat"):
        reasons.append("The session is Muhurat. Hours are not the regular cash session.")
    distance, floor = pack.get("circuit_distance_inr"), pack.get("min_circuit_distance_inr")
    if distance is not None and floor is not None and distance < floor:
        reasons.append(f"Circuit distance {distance} is inside the minimum {floor}.")
    if pack.get("ex_date_today") or pack.get("record_date_today") or pack.get("board_meeting_today"):
        reasons.append("The session is an ex-date, a record date, or a board meeting.")
    open_risk, limit = pack.get("open_risk_inr"), pack.get("daily_loss_limit_inr")
    if open_risk is not None and limit is not None and open_risk >= limit:
        reasons.append("Open planned risk has reached the daily loss limit.")


def _costs(pack: dict, reasons: list[str]) -> None:
    if not pack.get("costs_as_of"):
        reasons.append("The charge-sheet date was not checked.")
        return
    status = review_status(as_date(pack["costs_as_of"]))
    if not status["ok"]:
        reasons.append("The charge sheet is stale.")
