"""Dated charge sheet. A stale review date is a failed check, not a silent rate."""

from __future__ import annotations

import json
from datetime import date, timedelta

from indian_market.paths import data_dir


def load_costs() -> dict:
    return json.loads((data_dir() / "costs.json").read_text(encoding="utf-8"))


def charge_rate(item_id: str, as_of: date | None = None) -> dict:
    """One rate from the dated sheet. A stale review or a null rate does not invent a number."""
    status = review_status(as_of)
    on = date.fromisoformat(status["as_of"])
    if not status["ok"]:
        return {
            "ok": False,
            "detail": f"Charge sheet reviewed {status['last_reviewed']} is stale on {status['as_of']}.",
        }
    for item in status["items"]:
        if item["id"] != item_id:
            continue
        if item.get("rate") is None:
            return {"ok": False, "detail": f"{item_id} has no single rate. {item.get('source', '')}".strip()}
        effective = date.fromisoformat(item["effective_from"])
        if effective > on:
            return {"ok": False, "detail": f"{item_id} is effective from {item['effective_from']}."}
        return {
            "ok": True,
            "id": item_id,
            "rate": float(item["rate"]),
            "effective_from": item["effective_from"],
            "source": item.get("source") or "data/costs.json",
        }
    return {"ok": False, "detail": f"No charge named {item_id}."}


def stamp_rate(item_id: str, state: str | None, as_of: date | None = None) -> dict:
    """Uniform Article 56A rate, only after the buyer's state is named on the sheet."""
    status = review_status(as_of)
    if not status["ok"]:
        return {
            "ok": False,
            "detail": f"Charge sheet reviewed {status['last_reviewed']} is stale on {status['as_of']}.",
        }
    if not state or not str(state).strip():
        return {"ok": False, "detail": "Stamp duty needs the buyer's state. No rate is applied without it."}
    sheet = load_costs()
    known = {name.casefold(): name for name in sheet.get("stamp_states") or []}
    canonical = known.get(str(state).strip().casefold())
    if canonical is None:
        return {"ok": False, "detail": f"{state} is not on the stamp sheet."}
    on = date.fromisoformat(status["as_of"])
    for item in sheet.get("stamp_rates") or []:
        if item["id"] != item_id:
            continue
        if item.get("rate") is None:
            return {"ok": False, "detail": f"{item_id} has no rate."}
        effective = date.fromisoformat(item["effective_from"])
        if effective > on:
            return {"ok": False, "detail": f"{item_id} is effective from {item['effective_from']}."}
        return {
            "ok": True,
            "id": item_id,
            "rate": float(item["rate"]),
            "state": canonical,
            "effective_from": item["effective_from"],
            "source": item.get("source") or "data/costs.json",
        }
    return {"ok": False, "detail": f"No stamp rate named {item_id}."}


def review_status(as_of: date | None = None) -> dict:
    sheet = load_costs()
    as_of = as_of or date.today()
    reviewed = date.fromisoformat(sheet["last_reviewed"])
    horizon = int(sheet["review_horizon_days"])
    age = (as_of - reviewed).days
    return {
        "ok": 0 <= age <= horizon,
        "last_reviewed": sheet["last_reviewed"],
        "as_of": as_of.isoformat(),
        "age_days": age,
        "review_horizon_days": horizon,
        "stale_after": (reviewed + timedelta(days=horizon)).isoformat(),
        "note": sheet["note"],
        "items": sheet["items"],
    }
