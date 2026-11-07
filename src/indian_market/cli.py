"""Command line for the skill pack. JSON on stdout. Errors on stderr."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path

from indian_market.actions import read_actions, read_results
from indian_market.analysis import analyze
from indian_market.backtest import run_backtest
from indian_market.book import read_book
from indian_market.breadth import read_breadth
from indian_market.briefs import check_brief
from indian_market.calendar_in import IST, session_state
from indian_market.concall import read_concall
from indian_market.costs import review_status
from indian_market.desk import route_request
from indian_market.expiry import next_expiry
from indian_market.flows import read_flows
from indian_market.fundamentals import read_fundamentals
from indian_market.gate import assess_gate
from indian_market.journal import add_outcome, add_plan, review_journal, show_journal
from indian_market.levels import read_levels
from indian_market.morning import run_morning
from indian_market.official import KINDS, fetch_official, parse_official
from indian_market.options_book import read_options
from indian_market.paths import data_dir, fixtures_dir
from indian_market.plan import read_plan
from indian_market.premarket import build_premarket
from indian_market.rotation import read_rotation
from indian_market.scanner import scan_list
from indian_market.session_pack import build_session_pack
from indian_market.sizing import size_position
from indian_market.strategies import SETUPS
from indian_market.ticket import build_ticket
from indian_market.surveillance import clear
from indian_market.tape import read_tape
from indian_market.universe import resolve, series_report


def _print(payload: dict, code: int) -> int:
    json.dump(payload, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return code


def _load(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _demo(name: str) -> dict:
    return _load(fixtures_dir() / name)


def cmd_resolve(args: argparse.Namespace) -> int:
    payload = resolve(args.symbol, args.exchange)
    return _print(payload, 0 if payload["ok"] else 2)


def cmd_session(args: argparse.Namespace) -> int:
    now = datetime.fromisoformat(args.at) if args.at else None
    if now is not None and now.tzinfo is None:
        now = now.replace(tzinfo=IST)
    return _print(session_state(now, args.exchange), 0)


def cmd_expiry(args: argparse.Namespace) -> int:
    on = args.on or date.today().isoformat()
    payload = next_expiry(args.symbol, on)
    return _print(payload, 0 if payload["ok"] else 2)


def cmd_costs(_: argparse.Namespace) -> int:
    payload = review_status()
    return _print(payload, 0 if payload["ok"] else 1)


def cmd_surveillance(args: argparse.Namespace) -> int:
    facts = _demo("sail_ban.json") if args.demo else _load(args.fixture)
    resolved = resolve(facts["symbol"], facts.get("exchange"))
    if not resolved["ok"]:
        return _print(resolved, 2)
    payload = clear(facts, segment=args.segment)
    return _print(payload, 0)


def cmd_analyze(args: argparse.Namespace) -> int:
    pack = _demo("reliance_bars.json") if args.demo else _load(args.fixture)
    resolved = resolve(pack["symbol"], pack.get("exchange"))
    if not resolved["ok"]:
        return _print(resolved, 2)
    payload = analyze(pack)
    return _print(payload, 0 if payload["ok"] else 2)


def cmd_tape(args: argparse.Namespace) -> int:
    pack = _demo("reliance_tape.json") if args.demo else _load(args.fixture)
    resolved = resolve(pack["symbol"], pack.get("exchange"))
    if not resolved["ok"]:
        return _print(resolved, 2)
    payload = read_tape(pack)
    return _print(payload, 0 if payload["ok"] else 2)


def cmd_check_brief(args: argparse.Namespace) -> int:
    payload = check_brief(Path(args.path), args.kind)
    return _print(payload, 0 if payload["ok"] else 2)


def cmd_desk(args: argparse.Namespace) -> int:
    payload = route_request(args.text)
    return _print(payload, 0 if payload["ok"] else 2)


def _journal_path(args: argparse.Namespace) -> Path:
    return Path(args.path) if args.path else data_dir() / "journal.jsonl"


def cmd_journal_show(args: argparse.Namespace) -> int:
    if args.demo:
        payload = show_journal(fixtures_dir() / "journal_sample.jsonl")
        payload["detail"] = "Fixture journal. The live log was not read."
        return _print(payload, 0)
    return _print(show_journal(_journal_path(args)), 0)


def cmd_journal_add(args: argparse.Namespace) -> int:
    if args.demo:
        payload = show_journal(fixtures_dir() / "journal_sample.jsonl")
        payload["detail"] = "Demo does not append. Pass --fixture and optionally --path."
        return _print(payload, 0)
    pack = _load(args.fixture)
    payload = add_plan(_journal_path(args), pack, at=args.at)
    return _print(payload, 0 if payload.get("ok") else 2)


def cmd_journal_outcome(args: argparse.Namespace) -> int:
    if args.demo:
        return _print(
            {
                "ok": True,
                "wrote": False,
                "detail": "Demo does not append an outcome. The live journal was not written.",
            },
            0,
        )
    payload = add_outcome(
        _journal_path(args),
        args.id,
        args.outcome,
        at=args.at,
        source=args.source,
        realized_r=args.realized_r,
        exit_price=args.exit_price,
    )
    return _print(payload, 0 if payload.get("ok") else 2)


def cmd_journal_review(args: argparse.Namespace) -> int:
    if args.demo:
        path = fixtures_dir() / "journal_review.jsonl"
    elif args.path:
        path = Path(args.path)
    else:
        return _print(
            {
                "ok": False,
                "error": "no_evidence",
                "detail": "Pass --path or --demo. Demo does not write the journal.",
            },
            2,
        )
    payload = review_journal(path, as_of=args.as_of)
    return _print(payload, 0 if payload.get("ok") else 2)


_SETUP_DEMO = {
    "orb": "setup_orb.json",
    "pdh": "setup_pdh.json",
    "vwap": "setup_vwap.json",
    "delivery": "setup_delivery.json",
    "sector": "setup_sector.json",
    "post": "setup_post.json",
}

_FETCH_DEMO = {
    "cash_bhav": "official_cash.csv",
    "ban": "official_ban.csv",
    "contract": "official_contract.csv",
    "delivery": "official_delivery.csv",
    "constituents": "official_constituents.csv",
}


def cmd_setup(args: argparse.Namespace) -> int:
    runner = SETUPS.get(args.name)
    if runner is None:
        return _print(
            {
                "ok": False,
                "error": "bad_input",
                "detail": "Setup is orb, pdh, vwap, delivery, sector, or post.",
            },
            1,
        )
    return _run_pack(args, _SETUP_DEMO[args.name], runner, resolve_symbol=True)


def cmd_morning(args: argparse.Namespace) -> int:
    return _run_pack(args, "morning.json", run_morning, resolve_symbol=False)


def cmd_fetch(args: argparse.Namespace) -> int:
    session = args.session or "2026-11-06"
    if args.demo:
        filename = _FETCH_DEMO.get(args.kind)
        if filename is None:
            return _print(
                {
                    "ok": False,
                    "error": "no_evidence",
                    "detail": "Demo files exist for cash_bhav, ban, contract, delivery, and constituents. Pass --file for another kind.",
                },
                2,
            )
        path = fixtures_dir() / filename
        payload = parse_official(args.kind, path, session, source=f"fixture:{filename}")
        return _print(payload, 0 if payload.get("ok") else 2)
    if args.file:
        path = Path(args.file)
        payload = parse_official(args.kind, path, session, source=f"fixture:{path.name}")
        return _print(payload, 0 if payload.get("ok") else 2)
    if args.url:
        payload = fetch_official(args.kind, session, url=args.url)
        return _print(payload, 0 if payload.get("ok") else 2)
    return _print(
        {
            "ok": False,
            "error": "no_evidence",
            "detail": "Pass --file, --demo, or --url. This command does not guess a download.",
        },
        2,
    )


def cmd_series(args: argparse.Namespace) -> int:
    if args.demo:
        path = fixtures_dir() / "series_sample.csv"
    elif args.file:
        path = Path(args.file)
    else:
        return _print(
            {
                "ok": False,
                "error": "no_evidence",
                "detail": "Pass --file or --demo. The starter book is not rewritten.",
            },
            2,
        )
    payload = series_report(path)
    return _print(payload, 0 if payload.get("ok") else 2)


def cmd_ticket(args: argparse.Namespace) -> int:
    pack = _demo("ticket_reliance.json") if args.demo else _load(args.fixture)
    resolved = resolve(pack["symbol"], pack.get("exchange"))
    if not resolved["ok"]:
        return _print(resolved, 2)
    pack = dict(pack)
    pack["symbol"] = resolved["symbol"]
    pack["exchange"] = resolved["exchange"]
    pack.setdefault("series", resolved.get("series"))
    if args.path and not args.demo:
        pack["journal_path"] = args.path
    payload = build_ticket(pack)
    return _print(payload, 0 if payload.get("ok") else 2)


def cmd_session_pack(args: argparse.Namespace) -> int:
    if args.demo:
        directory = fixtures_dir() / "session_sample"
    elif args.directory:
        directory = Path(args.directory)
    else:
        return _print(
            {
                "ok": False,
                "error": "no_evidence",
                "detail": "Pass --dir or --demo. A missing file stays blank. This command does not download.",
            },
            2,
        )
    payload = build_session_pack(directory, session=args.session, symbol=args.symbol)
    return _print(payload, 0 if payload.get("ok") else 2)


def _run_pack(args: argparse.Namespace, demo_name: str, fn, *, resolve_symbol: bool) -> int:
    pack = _demo(demo_name) if args.demo else _load(args.fixture)
    mandate = getattr(args, "mandate", None)
    if mandate:
        loaded = json.loads(Path(mandate).read_text(encoding="utf-8"))
        pack = dict(pack)
        pack["mandate"] = loaded
    if resolve_symbol:
        resolved = resolve(pack["symbol"], pack.get("exchange"))
        if not resolved["ok"]:
            return _print(resolved, 2)
        pack = dict(pack)
        pack["symbol"] = resolved["symbol"]
        pack["exchange"] = resolved["exchange"]
        pack.setdefault("series", resolved.get("series"))
    payload = fn(pack)
    if payload.get("error") == "outside_universe":
        return _print(payload, 2)
    return _print(payload, 0 if payload.get("ok") else 2)


_PACKS = (
    ("premarket", "premarket.json", build_premarket, False),
    ("flows", "flows.json", read_flows, False),
    ("breadth", "breadth.json", read_breadth, False),
    ("rotation", "rotation.json", read_rotation, False),
    ("options", "options_nifty.json", read_options, True),
    ("levels", "levels_reliance.json", read_levels, True),
    ("fundamentals", "fundamentals_reliance.json", read_fundamentals, True),
    ("concall", "concall_reliance.json", read_concall, True),
    ("actions", "actions_reliance.json", read_actions, True),
    ("results", "results_calendar.json", read_results, False),
    ("plan", "plan_reliance.json", read_plan, True),
    ("size", "size_reliance.json", size_position, True),
    ("gate", "gate_pass.json", assess_gate, True),
    ("scan", "scan_list.json", scan_list, False),
    ("backtest", "backtest_reliance.json", run_backtest, True),
    ("book", "book.json", read_book, False),
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m indian_market.cli")
    sub = parser.add_subparsers(dest="command", required=True)

    resolve_cmd = sub.add_parser("resolve")
    resolve_cmd.add_argument("symbol")
    resolve_cmd.add_argument("--exchange")
    resolve_cmd.set_defaults(func=cmd_resolve)

    session_cmd = sub.add_parser("session")
    session_cmd.add_argument("--at", help="ISO datetime. Naive values are read as IST.")
    session_cmd.add_argument("--exchange", default="NSE")
    session_cmd.set_defaults(func=cmd_session)

    expiry_cmd = sub.add_parser("expiry")
    expiry_cmd.add_argument("symbol")
    expiry_cmd.add_argument("--on")
    expiry_cmd.set_defaults(func=cmd_expiry)

    costs_cmd = sub.add_parser("costs")
    costs_cmd.set_defaults(func=cmd_costs)

    surveillance_cmd = sub.add_parser("surveillance")
    surveillance_cmd.add_argument("--fixture")
    surveillance_cmd.add_argument("--demo", action="store_true")
    surveillance_cmd.add_argument("--segment", default="cash", choices=("cash", "fo"))
    surveillance_cmd.set_defaults(func=cmd_surveillance)

    analyze_cmd = sub.add_parser("analyze")
    analyze_cmd.add_argument("--fixture")
    analyze_cmd.add_argument("--demo", action="store_true")
    analyze_cmd.set_defaults(func=cmd_analyze)

    tape_cmd = sub.add_parser("tape")
    tape_cmd.add_argument("--fixture")
    tape_cmd.add_argument("--demo", action="store_true")
    tape_cmd.set_defaults(func=cmd_tape)

    brief_cmd = sub.add_parser("check-brief")
    brief_cmd.add_argument("path")
    brief_cmd.add_argument("--kind", required=True, choices=("research", "swot", "concall", "thesis", "short", "ic"))
    brief_cmd.set_defaults(func=cmd_check_brief)

    desk_cmd = sub.add_parser("desk")
    desk_cmd.add_argument("text")
    desk_cmd.set_defaults(func=cmd_desk)

    ticket_cmd = sub.add_parser("ticket")
    ticket_cmd.add_argument("--fixture")
    ticket_cmd.add_argument("--demo", action="store_true")
    ticket_cmd.add_argument("--path", help="Append the human yes to this journal. Demo does not write.")
    ticket_cmd.set_defaults(func=cmd_ticket)

    journal_show = sub.add_parser("journal-show")
    journal_show.add_argument("--path")
    journal_show.add_argument("--demo", action="store_true")
    journal_show.set_defaults(func=cmd_journal_show)

    journal_add = sub.add_parser("journal-add")
    journal_add.add_argument("--fixture")
    journal_add.add_argument("--demo", action="store_true")
    journal_add.add_argument("--path")
    journal_add.add_argument("--at")
    journal_add.set_defaults(func=cmd_journal_add)

    journal_outcome = sub.add_parser("journal-outcome")
    journal_outcome.add_argument("--path")
    journal_outcome.add_argument("--id", required=True)
    journal_outcome.add_argument("--outcome", required=True)
    journal_outcome.add_argument("--at")
    journal_outcome.add_argument("--source")
    journal_outcome.add_argument("--demo", action="store_true")
    journal_outcome.add_argument("--realized-r", dest="realized_r", type=float)
    journal_outcome.add_argument("--exit-price", dest="exit_price", type=float)
    journal_outcome.set_defaults(func=cmd_journal_outcome)

    journal_review = sub.add_parser("journal-review")
    journal_review.add_argument("--path")
    journal_review.add_argument("--demo", action="store_true")
    journal_review.add_argument("--as-of", dest="as_of")
    journal_review.set_defaults(func=cmd_journal_review)

    setup_cmd = sub.add_parser("setup")
    setup_cmd.add_argument("--name", required=True, choices=tuple(SETUPS))
    setup_cmd.add_argument("--fixture")
    setup_cmd.add_argument("--demo", action="store_true")
    setup_cmd.set_defaults(func=cmd_setup)

    morning_cmd = sub.add_parser("morning")
    morning_cmd.add_argument("--fixture")
    morning_cmd.add_argument("--demo", action="store_true")
    morning_cmd.set_defaults(func=cmd_morning)

    fetch_cmd = sub.add_parser("fetch")
    fetch_cmd.add_argument("--kind", required=True, choices=tuple(KINDS))
    fetch_cmd.add_argument("--session")
    fetch_cmd.add_argument("--file")
    fetch_cmd.add_argument("--url")
    fetch_cmd.add_argument("--demo", action="store_true")
    fetch_cmd.set_defaults(func=cmd_fetch)

    series_cmd = sub.add_parser("series")
    series_cmd.add_argument("--file")
    series_cmd.add_argument("--demo", action="store_true")
    series_cmd.set_defaults(func=cmd_series)

    session_pack_cmd = sub.add_parser("session-pack")
    session_pack_cmd.add_argument("--dir", dest="directory")
    session_pack_cmd.add_argument("--demo", action="store_true")
    session_pack_cmd.add_argument("--session")
    session_pack_cmd.add_argument("--symbol")
    session_pack_cmd.set_defaults(func=cmd_session_pack)

    for name, demo_name, fn, resolve_symbol in _PACKS:
        pack_cmd = sub.add_parser(name)
        pack_cmd.add_argument("--fixture")
        pack_cmd.add_argument("--demo", action="store_true")
        pack_cmd.add_argument("--mandate", help="Merge this mandate file into the pack. A missing file is not loaded.")
        pack_cmd.set_defaults(
            func=lambda args, demo_name=demo_name, fn=fn, resolve_symbol=resolve_symbol: _run_pack(
                args, demo_name, fn, resolve_symbol=resolve_symbol
            )
        )

    args = parser.parse_args(argv)
    evidence_commands = {
        "surveillance",
        "analyze",
        "tape",
        "ticket",
        "journal-add",
        "setup",
        "morning",
        *(name for name, *_rest in _PACKS),
    }
    if getattr(args, "fixture", None) is None and getattr(args, "demo", False) is False:
        if args.command in evidence_commands:
            return _print(
                {
                    "ok": False,
                    "error": "no_evidence",
                    "detail": "Pass --fixture PATH or --demo. This command does not invent prices.",
                },
                2,
            )
    try:
        return args.func(args)
    except (OSError, json.JSONDecodeError, KeyError, ValueError) as exc:
        return _print({"ok": False, "error": "bad_input", "detail": str(exc)}, 1)


if __name__ == "__main__":
    sys.exit(main())
