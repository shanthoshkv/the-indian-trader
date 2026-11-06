"""Dated charge sheet. A stale review date is a failed check, not a silent rate."""

from __future__ import annotations

import json
from datetime import date, timedelta

from indian_market.paths import data_dir


def load_costs() -> dict:
    return json.loads((data_dir() / "costs.json").read_text(encoding="utf-8"))


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
