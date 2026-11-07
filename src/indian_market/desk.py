"""Route a question to one skill. This module does not compute a market figure."""

from __future__ import annotations

import re

# Longer, specific phrases carry more weight than a single shared word.
_RULES: tuple[tuple[str, str, int], ...] = (
    ("swot", "swot-analysis", 8),
    ("read the tape", "tape-reading", 8),
    ("opening range", "tape-reading", 7),
    ("tape", "tape-reading", 5),
    ("vwap", "tape-reading", 5),
    ("ticks", "tape-reading", 5),
    ("trade-for-trade", "surveillance-check", 8),
    ("trade for trade", "surveillance-check", 8),
    ("surveillance", "surveillance-check", 6),
    ("asm", "surveillance-check", 5),
    ("gsm", "surveillance-check", 5),
    ("esm", "surveillance-check", 5),
    ("ban", "surveillance-check", 4),
    ("premarket", "premarket-brief", 8),
    ("pre-market", "premarket-brief", 8),
    ("morning brief", "premarket-brief", 8),
    ("gift nifty", "premarket-brief", 8),
    ("gift", "premarket-brief", 5),
    ("fii", "institutional-flows", 5),
    ("dii", "institutional-flows", 5),
    ("fpi", "institutional-flows", 5),
    ("bulk deal", "institutional-flows", 7),
    ("block deal", "institutional-flows", 7),
    ("participant", "institutional-flows", 4),
    ("advance decline", "market-breadth", 8),
    ("advances", "market-breadth", 5),
    ("declines", "market-breadth", 5),
    ("breadth", "market-breadth", 6),
    ("new highs", "market-breadth", 6),
    ("new lows", "market-breadth", 6),
    ("sector rotation", "sector-rotation", 8),
    ("sector index", "sector-rotation", 7),
    ("which sector", "sector-rotation", 6),
    ("put call", "options-positioning", 8),
    ("put-call", "options-positioning", 8),
    ("pcr", "options-positioning", 8),
    ("option chain", "options-positioning", 8),
    ("open interest", "options-positioning", 4),
    ("lot size", "options-positioning", 5),
    ("freeze", "options-positioning", 5),
    ("days to expiry", "options-positioning", 7),
    ("india vix", "options-positioning", 3),
    ("india vix", "premarket-brief", 3),
    ("central pivot", "levels-plan", 8),
    ("cpr", "levels-plan", 6),
    ("pivot", "levels-plan", 5),
    ("levels", "levels-plan", 5),
    ("fundamentals", "fundamentals", 8),
    ("pledge", "fundamentals", 6),
    ("shareholding", "fundamentals", 5),
    ("roe", "fundamentals", 4),
    ("concall", "concall-reader", 8),
    ("transcript", "concall-reader", 6),
    ("capex", "concall-reader", 5),
    ("guidance", "concall-reader", 4),
    ("corporate action", "corporate-actions", 8),
    ("ex-date", "corporate-actions", 7),
    ("ex date", "corporate-actions", 7),
    ("dividend", "corporate-actions", 6),
    ("buyback", "corporate-actions", 6),
    ("bonus", "corporate-actions", 4),
    ("rights", "corporate-actions", 4),
    ("split", "corporate-actions", 3),
    ("ofs", "corporate-actions", 5),
    ("results calendar", "results-calendar", 8),
    ("upcoming results", "results-calendar", 8),
    ("board meeting", "results-calendar", 5),
    ("research brief", "market-research", 8),
    ("what does", "market-research", 6),
    ("peers", "market-research", 5),
    ("relative strength", "market-analysis", 7),
    ("buildup", "market-analysis", 6),
    ("delivery", "market-analysis", 5),
    ("muhurat", "market-core", 7),
    ("holiday", "market-core", 4),
    ("pre-open", "market-core", 5),
    ("stt", "market-core", 6),
    ("expiry", "market-core", 4),
    ("which exchange", "market-core", 6),
    ("trade plan", "trade-plan", 8),
    ("plan the trade", "trade-plan", 8),
    ("position size", "position-size", 8),
    ("how many shares", "position-size", 7),
    ("risk gate", "risk-gate", 8),
    ("trade journal", "trade-journal", 8),
    ("journal", "trade-journal", 6),
    ("scan the list", "scanner", 8),
    ("opening range break", "scanner", 8),
    ("scanner", "scanner", 8),
    ("backtest", "backtest-india", 8),
    ("paper ticket", "paper-ticket", 8),
    ("manual ticket", "paper-ticket", 8),
    ("orb setup", "opening-range-break", 9),
    ("opening range strategy", "opening-range-break", 9),
    ("previous day break", "previous-day-break", 9),
    ("previous-day break", "previous-day-break", 9),
    ("vwap hold", "vwap-hold", 9),
    ("delivery and relative strength", "delivery-rs", 13),
    ("sector leader", "sector-leader", 9),
    ("post result", "post-result", 9),
    ("post-result", "post-result", 9),
    ("morning chain", "morning-chain", 9),
    ("journal review", "journal-review", 9),
    ("bhav copy", "official-files", 8),
    ("official file", "official-files", 8),
    ("series report", "official-files", 8),
)

_COMMAND = {
    "market-core": "resolve",
    "surveillance-check": "surveillance",
    "market-research": "check-brief",
    "market-analysis": "analyze",
    "swot-analysis": "check-brief",
    "tape-reading": "tape",
    "premarket-brief": "premarket",
    "institutional-flows": "flows",
    "market-breadth": "breadth",
    "sector-rotation": "rotation",
    "options-positioning": "options",
    "levels-plan": "levels",
    "fundamentals": "fundamentals",
    "concall-reader": "concall",
    "corporate-actions": "actions",
    "results-calendar": "results",
    "trade-plan": "plan",
    "position-size": "size",
    "risk-gate": "gate",
    "trade-journal": "journal-show",
    "scanner": "scan",
    "backtest-india": "backtest",
    "paper-ticket": "ticket",
    "opening-range-break": "setup",
    "previous-day-break": "setup",
    "vwap-hold": "setup",
    "delivery-rs": "setup",
    "sector-leader": "setup",
    "post-result": "setup",
    "morning-chain": "morning",
    "journal-review": "journal-review",
    "official-files": "fetch",
}


def _hit(text: str, phrase: str) -> bool:
    if " " in phrase or "-" in phrase:
        return phrase in text
    return re.search(rf"\b{re.escape(phrase)}\b", text) is not None


def route_request(text: str) -> dict:
    lowered = (text or "").lower()
    scores: dict[str, int] = {}
    if not lowered.strip():
        return {
            "ok": False,
            "error": "no_route",
            "candidates": [],
            "detail": "No question was given. Name the job, or ask again.",
        }
    for phrase, skill, weight in _RULES:
        if _hit(lowered, phrase):
            scores[skill] = scores.get(skill, 0) + weight
    if not scores:
        return {
            "ok": False,
            "error": "no_route",
            "candidates": [],
            "detail": "No skill in this pack matches. Do not invent the figure.",
        }
    best = max(scores.values())
    winners = sorted(skill for skill, score in scores.items() if score == best)
    if len(winners) > 1:
        return {
            "ok": False,
            "error": "ambiguous",
            "candidates": winners,
            "detail": "More than one skill matches. Ask which job, then run that skill.",
        }
    skill = winners[0]
    return {
        "ok": True,
        "skill": skill,
        "command": _COMMAND[skill],
        "detail": "Open that skill and run its command. This router does not compute the figure.",
    }
