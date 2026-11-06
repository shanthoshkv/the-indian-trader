"""Command line for the skill pack. JSON on stdout. Errors on stderr."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path

from indian_market.analysis import analyze
from indian_market.briefs import check_brief
from indian_market.calendar_in import IST, session_state
from indian_market.costs import review_status
from indian_market.expiry import next_expiry
from indian_market.paths import fixtures_dir
from indian_market.surveillance import clear
from indian_market.tape import read_tape
from indian_market.universe import resolve


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
    brief_cmd.add_argument("--kind", required=True, choices=("research", "swot"))
    brief_cmd.set_defaults(func=cmd_check_brief)

    args = parser.parse_args(argv)
    if getattr(args, "fixture", None) is None and getattr(args, "demo", False) is False:
        if args.command in {"surveillance", "analyze", "tape"}:
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
