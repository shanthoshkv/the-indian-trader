"""Turn one session folder of files the user already has into evidence rows.

A missing file stays a blank block. This does not invent a price and it does not run a ticket.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from indian_market.evidence import evidence, missing
from indian_market.official import KINDS, parse_official
from indian_market.records import done, freshness_for

_NAMES = {
    "cash_bhav": ("cash_bhav.csv", "bhav.csv"),
    "fo_bhav": ("fo_bhav.csv",),
    "ban": ("ban.csv",),
    "contract": ("contract.csv",),
    "flows": ("flows.csv",),
    "announcements": ("announcements.csv",),
    "delivery": ("delivery.csv",),
    "bulk_deals": ("bulk_deals.csv",),
    "block_deals": ("block_deals.csv",),
    "asm": ("asm.csv",),
    "gsm": ("gsm.csv",),
    "esm": ("esm.csv",),
    "mwpl": ("mwpl.csv",),
    "shareholding": ("shareholding.csv",),
    "pledge": ("pledge.csv",),
    "constituents": ("constituents.csv",),
}


def build_session_pack(directory: Path, session: str | None = None, symbol: str | None = None) -> dict[str, Any]:
    if not directory.is_dir():
        detail = "The session folder is not there. Nothing was guessed."
        return {
            "ok": False,
            "error": "no_evidence",
            "detail": detail,
            "items": [missing(symbol=symbol or "NSE", exchange="NSE", field="session_pack", source="fixture:session", detail=detail)],
        }
    session = session or _session_from_name(directory.name)
    source = f"fixture:{directory.name}"
    items: list[dict[str, Any]] = []
    found: list[str] = []
    missing_kinds: list[str] = []
    for kind in KINDS:
        path = _find(directory, kind)
        if path is None:
            missing_kinds.append(kind)
            items.append(missing(symbol=symbol or "NSE", exchange="NSE", field=f"session_{kind}", source=source, detail=f"No {kind} file in the session folder."))
            continue
        found.append(kind)
        parsed = parse_official(kind, path, session, source=source)
        items.extend(parsed.get("items") or [])
    if symbol:
        _named(items, symbol, found, source, session)
    return done(items, session_date=session, files_found=found, files_missing=missing_kinds)


def _named(items, symbol, found, source, session) -> None:
    """A surveillance fragment only when the asked name is in the ban or ASM file."""
    name = str(symbol).strip().upper()
    if not name:
        return
    if "ban" in found and any(
        row.get("ok") and row.get("field") == "fo_ban" and str(row.get("symbol") or "").upper() == name
        for row in items
    ):
        _named_row(items, name, "named_fo_ban", True, source, session, "Named in the session ban file.")
    stage = next(
        (
            row.get("value")
            for row in items
            if row.get("ok") and row.get("field") == "asm_stage" and str(row.get("symbol") or "").upper() == name
        ),
        None,
    )
    if "asm" in found and stage is not None:
        _named_row(items, name, "named_asm_stage", stage, source, session, "Named in the session ASM file.")


def _named_row(items, name, field, value, source, session, detail) -> None:
    items.append(
        evidence(
            symbol=name,
            exchange="NSE",
            field=field,
            value=value,
            unit="label",
            session_date=session,
            as_of_ist=None,
            source=source,
            freshness=freshness_for(source, "previous_session"),
            detail=detail,
        )
    )


def _session_from_name(name: str) -> str:
    if len(name) == 10 and name[4] == "-" and name[7] == "-":
        return name
    return "unset"


def _find(directory: Path, kind: str) -> Path | None:
    for name in _NAMES.get(kind, ()):
        path = directory / name
        if path.is_file():
            return path
    return None
