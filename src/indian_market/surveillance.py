"""Clearance before trade language. Cash research of a banned name stays allowed."""

from __future__ import annotations

from typing import Any


def clear(facts: dict[str, Any], *, segment: str = "cash") -> dict[str, Any]:
    """segment is cash or fo. A ban blocks fresh F&O and only cautions cash."""
    symbol = facts["symbol"]
    exchange = facts["exchange"]
    series = (facts.get("series") or "EQ").upper()
    segment = segment.lower()
    flags: list[str] = []

    if facts.get("fo_ban"):
        flags.append("F&O ban: fresh derivative positions are blocked. Cash can still trade.")
    if facts.get("trade_for_trade") or series == "BE":
        flags.append(f"Series {series} trades for trade. Intraday square-off is not available.")
    if series in {"SM", "ST", "SZ"}:
        flags.append(f"Series {series} is an SME listing. Liquidity is usually thin.")
    if series == "BZ":
        flags.append("Series BZ. Confirm the surveillance stage before sizing a trade.")
    for key, label in (("asm_stage", "ASM"), ("gsm_stage", "GSM")):
        stage = facts.get(key)
        if stage:
            flags.append(f"{label} stage {stage}.")
    if facts.get("esm"):
        flags.append("ESM is on.")
    if facts.get("near_circuit"):
        flags.append("Previous close is near the price band.")

    if segment == "fo" and facts.get("fo_ban"):
        status = "blocked"
    elif not flags:
        status = "clear"
    else:
        status = "caution"

    return {
        "ok": True,
        "symbol": symbol,
        "exchange": exchange,
        "series": series,
        "segment": segment,
        "clearance": status,
        "flags": flags,
        "session_date": facts.get("session_date"),
        "source": facts.get("source"),
        "freshness": facts.get("freshness", "previous_session"),
        "lot_size": facts.get("lot_size"),
        "price_band_pct": facts.get("price_band_pct"),
    }
