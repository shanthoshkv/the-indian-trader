import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import date, datetime
from pathlib import Path

import _path  # noqa: F401

from indian_market.actions import read_actions, read_results
from indian_market.analysis import analyze, oi_quadrant
from indian_market.backtest import run_backtest
from indian_market.breadth import read_breadth
from indian_market.briefs import check_brief
from indian_market.concall import read_concall
from indian_market.desk import route_request
from indian_market.flows import read_flows
from indian_market.fundamentals import read_fundamentals
from indian_market.gate import assess_gate
from indian_market.journal import add_outcome, add_plan, open_risk_inr, review_journal, show_journal
from indian_market.levels import read_levels
from indian_market.options_book import read_options
from indian_market.plan import read_plan
from indian_market.premarket import build_premarket
from indian_market.rotation import read_rotation
from indian_market.scanner import scan_list
from indian_market.sizing import size_position
from indian_market.ticket import build_ticket
from indian_market.calendar_in import IST, is_trading_day, next_trading_day, session_state
from indian_market.cli import main
from indian_market.costs import review_status
from indian_market.expiry import next_expiry
from indian_market.paths import fixtures_dir, repo_root
from indian_market.surveillance import clear
from indian_market.tape import read_tape
from indian_market.morning import run_morning
from indian_market.official import fetch_official, parse_official
from indian_market.strategies import delivery_rs, opening_range_break, post_result, previous_day_break, sector_leader, vwap_hold
from indian_market.universe import resolve, series_report

ROOT = repo_root()


class UniverseTests(unittest.TestCase):
    def test_reliance_defaults_to_nse(self):
        got = resolve("reliance")
        self.assertTrue(got["ok"])
        self.assertEqual(got["exchange"], "NSE")
        self.assertEqual(got["bse_code"], "500325")
        self.assertTrue(got["verified"])

    def test_reliance_bse_keeps_the_scrip_code(self):
        got = resolve("RELIANCE", "BSE")
        self.assertEqual(got["exchange"], "BSE")
        self.assertEqual(got["bse_code"], "500325")

    def test_suffixes(self):
        self.assertEqual(resolve("TCS.NS")["exchange"], "NSE")
        self.assertEqual(resolve("TCS.BO")["exchange"], "BSE")

    def test_indexes(self):
        self.assertEqual(resolve("NIFTY")["exchange"], "NSE")
        self.assertEqual(resolve("SENSEX")["exchange"], "BSE")
        self.assertEqual(resolve("bank nifty")["symbol"], "BANKNIFTY")

    def test_us_ticker_is_refused(self):
        got = resolve("AAPL")
        self.assertFalse(got["ok"])
        self.assertEqual(got["error"], "outside_universe")

    def test_mcx_exchange_is_refused(self):
        got = resolve("CRUDEOIL", "MCX")
        self.assertFalse(got["ok"])

    def test_unknown_nse_symbol_is_unverified(self):
        got = resolve("ZYDUSLIFE")
        self.assertTrue(got["ok"])
        self.assertFalse(got["verified"])
        self.assertEqual(got["exchange"], "NSE")


class CalendarTests(unittest.TestCase):
    def test_continuous_session(self):
        now = datetime(2026, 11, 6, 10, 0, tzinfo=IST)
        self.assertEqual(session_state(now)["phase"], "continuous")

    def test_preopen_limit_window(self):
        now = datetime(2026, 11, 6, 9, 7, tzinfo=IST)
        self.assertEqual(session_state(now)["phase"], "preopen_limit")

    def test_diwali_closure(self):
        now = datetime(2026, 11, 10, 10, 0, tzinfo=IST)
        state = session_state(now)
        self.assertEqual(state["phase"], "holiday")
        self.assertIn("Balipratipada", state["name"])

    def test_muhurat_window(self):
        during = datetime(2026, 11, 8, 14, 30, tzinfo=IST)
        before = datetime(2026, 11, 8, 10, 0, tzinfo=IST)
        self.assertEqual(session_state(during)["phase"], "muhurat")
        self.assertEqual(session_state(before)["phase"], "closed")

    def test_bse_only_january_election(self):
        day = date(2026, 1, 15)
        self.assertFalse(is_trading_day(day, "BSE"))
        self.assertTrue(is_trading_day(day, "NSE"))

    def test_naive_datetime_is_ist(self):
        now = datetime(2026, 11, 6, 16, 0)
        self.assertEqual(session_state(now)["phase"], "closed")


class ExpiryTests(unittest.TestCase):
    def test_nifty_weekly_shifts_off_diwali_tuesday(self):
        got = next_expiry("NIFTY", "2026-11-06")
        self.assertEqual(got["weekly"], "2026-11-09")
        self.assertEqual(got["monthly"], "2026-11-23")

    def test_sensex_weekly_is_thursday(self):
        got = next_expiry("SENSEX", "2026-11-06")
        self.assertEqual(got["weekly"], "2026-11-12")

    def test_banknifty_has_no_weekly(self):
        got = next_expiry("BANKNIFTY", "2026-11-06")
        self.assertIsNone(got["weekly"])
        self.assertEqual(got["monthly"], "2026-11-23")

    def test_sensex_shifts_off_bakri_id(self):
        got = next_expiry("SENSEX", "2026-05-27")
        self.assertEqual(got["weekly"], "2026-05-27")

    def test_us_index_has_no_expiry_here(self):
        got = next_expiry("SPY", "2026-11-06")
        self.assertFalse(got["ok"])

    def test_stock_alias_is_not_given_a_nifty_weekly(self):
        got = next_expiry("STOCK", "2026-11-06")
        self.assertFalse(got["ok"])
        self.assertEqual(got["error"], "outside_universe")


class CostTests(unittest.TestCase):
    def test_review_is_current_on_the_snapshot_date(self):
        status = review_status(date(2026, 11, 6))
        self.assertTrue(status["ok"])

    def test_review_goes_stale(self):
        status = review_status(date(2027, 6, 1))
        self.assertFalse(status["ok"])


class SurveillanceTests(unittest.TestCase):
    def test_ban_cautions_cash_and_blocks_fo(self):
        facts = {
            "symbol": "SAIL",
            "exchange": "NSE",
            "series": "EQ",
            "fo_ban": True,
            "session_date": "2026-11-05",
            "source": "fixture:ban",
        }
        self.assertEqual(clear(facts, segment="cash")["clearance"], "caution")
        self.assertEqual(clear(facts, segment="fo")["clearance"], "blocked")

    def test_trade_for_trade(self):
        facts = {"symbol": "X", "exchange": "NSE", "series": "BE", "trade_for_trade": True}
        self.assertEqual(clear(facts)["clearance"], "caution")


class AnalysisTests(unittest.TestCase):
    def test_quadrants(self):
        self.assertEqual(oi_quadrant(1, 1), "long_buildup")
        self.assertEqual(oi_quadrant(-1, 1), "short_buildup")
        self.assertEqual(oi_quadrant(-1, -1), "long_unwinding")
        self.assertEqual(oi_quadrant(1, -1), "short_covering")

    def test_demo_pack(self):
        import json

        pack = json.loads((fixtures_dir() / "reliance_bars.json").read_text(encoding="utf-8"))
        got = analyze(pack)
        fields = {item["field"]: item for item in got["items"]}
        self.assertEqual(fields["close"]["value"], 108.0)
        self.assertEqual(fields["delivery_pct"]["value"], 50.0)
        self.assertFalse(fields["return_20d_pct"]["ok"])
        self.assertGreater(fields["rs_vs_benchmark_pct"]["value"], 0)
        self.assertEqual(fields["fut_oi_quadrant"]["value"], "long_buildup")
        self.assertEqual(fields["close"]["source"], "fixture:nse-cm-bhavcopy")


class TapeTests(unittest.TestCase):
    def test_opening_range_excludes_the_0930_bar(self):
        import json

        pack = json.loads((fixtures_dir() / "reliance_tape.json").read_text(encoding="utf-8"))
        got = read_tape(pack)
        fields = {item["field"]: item for item in got["items"]}
        self.assertEqual(fields["tape_mode"]["value"], "session")
        self.assertEqual(fields["opening_range_high"]["value"], 109.2)
        self.assertEqual(fields["opening_range_low"]["value"], 107.6)
        self.assertEqual(fields["last_vs_vwap"]["value"], "above")
        self.assertEqual(fields["delivery_pct"]["freshness"], "previous_session")

    def test_prints_without_a_feed_stay_blank(self):
        got = read_tape({"symbol": "RELIANCE", "exchange": "NSE", "mode": "prints", "source": "none"})
        prints = next(item for item in got["items"] if item["field"] == "prints")
        self.assertFalse(prints["ok"])
        self.assertIsNone(prints["value"])


class BriefTests(unittest.TestCase):
    def test_sourced_research_passes(self):
        got = check_brief(fixtures_dir() / "reliance_research_ok.md", "research")
        self.assertTrue(got["ok"], got["problems"])

    def test_unsourced_research_fails(self):
        got = check_brief(fixtures_dir() / "reliance_research_bad.md", "research")
        self.assertFalse(got["ok"])
        self.assertTrue(any("source" in problem for problem in got["problems"]))
        self.assertTrue(any("buy" in problem.lower() for problem in got["problems"]))


class CliTests(unittest.TestCase):
    def _run(self, argv):
        with redirect_stdout(io.StringIO()):
            return main(argv)

    def test_resolve_refusal_exits_2(self):
        self.assertEqual(self._run(["resolve", "TSLA"]), 2)

    def test_analyze_demo_exits_0(self):
        self.assertEqual(self._run(["analyze", "--demo"]), 0)

    def test_analyze_without_evidence_exits_2(self):
        self.assertEqual(self._run(["analyze"]), 2)

    def test_check_brief(self):
        path = str(fixtures_dir() / "reliance_research_ok.md")
        self.assertEqual(self._run(["check-brief", path, "--kind", "research"]), 0)

    def test_phase2_and_3_demos_exit_0_and_refuse_a_missing_file(self):
        commands = (
            "premarket",
            "flows",
            "breadth",
            "rotation",
            "options",
            "levels",
            "fundamentals",
            "concall",
            "actions",
            "results",
        )
        for command in commands:
            self.assertEqual(self._run([command, "--demo"]), 0, command)
            self.assertEqual(self._run([command]), 2, command)

    def test_desk_command(self):
        self.assertEqual(self._run(["desk", "read the tape on RELIANCE"]), 0)
        self.assertEqual(self._run(["desk", "hello there"]), 2)

    def test_phase4_and_5_demos_exit_0_and_refuse_a_missing_file(self):
        commands = ("plan", "size", "gate", "scan", "backtest", "ticket", "journal-add")
        for command in commands:
            self.assertEqual(self._run([command, "--demo"]), 0, command)
            self.assertEqual(self._run([command]), 2, command)
        for command in ("morning", "journal-review", "series"):
            self.assertEqual(self._run([command, "--demo"]), 0, command)
            self.assertEqual(self._run([command]), 2, command)
        self.assertEqual(self._run(["setup", "--name", "orb", "--demo"]), 0)
        self.assertEqual(self._run(["setup", "--name", "orb"]), 2)
        self.assertEqual(self._run(["fetch", "--kind", "cash_bhav", "--demo"]), 0)
        self.assertEqual(self._run(["fetch", "--kind", "cash_bhav"]), 2)
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main(["journal-show", "--demo"])
        self.assertEqual(code, 0)
        shown = json.loads(buf.getvalue())
        self.assertIn("Fixture journal", shown["detail"])
        self.assertEqual(shown["entries"][0]["outcome"], "open")


def _load(name):
    return json.loads((fixtures_dir() / name).read_text(encoding="utf-8"))


def _one(payload, field, symbol=None):
    rows = [
        row
        for row in payload["items"]
        if row["field"] == field and (symbol is None or row["symbol"] == symbol)
    ]
    if len(rows) != 1:
        raise AssertionError(f"{field} {symbol}: {rows}")
    return rows[0]


class Phase2Tests(unittest.TestCase):
    def test_preopen_stays_blank_before_0900(self):
        payload = build_premarket(_load("premarket.json"))
        preopen = _one(payload, "preopen", "NIFTY")
        self.assertFalse(preopen["ok"])
        self.assertEqual(_one(payload, "weekly_expiry", "NIFTY")["value"], "2026-11-09")
        self.assertEqual(_one(payload, "weekly_expiry", "SENSEX")["value"], "2026-11-12")
        fii = _one(payload, "fii_cash_net", "FII")
        self.assertEqual(fii["freshness"], "previous_session")
        self.assertEqual(fii["session_date"], "2026-11-05")
        gift = _one(payload, "gift_nifty", "GIFTNIFTY")
        self.assertTrue(gift["ok"])
        self.assertIn("Not an NSE or BSE cash print", gift["detail"])
        self.assertEqual(gift["exchange"], "GIFT")

    def test_preopen_prints_after_0900_and_gift_cannot_be_labeled_nse(self):
        pack = _load("premarket.json")
        pack["as_of_ist"] = "2026-11-06T09:08:00+05:30"
        printed = build_premarket(pack)
        self.assertTrue(_one(printed, "preopen", "NIFTY")["ok"])
        self.assertEqual(_one(printed, "preopen", "NIFTY")["value"], 25580.0)
        pack["gift_nifty"]["exchange"] = "NSE"
        refused = build_premarket(pack)
        self.assertFalse(_one(refused, "gift_nifty")["ok"])

    def test_preopen_is_blank_on_a_holiday(self):
        pack = _load("premarket.json")
        pack["session_date"] = "2026-11-10"
        pack["as_of_ist"] = "2026-11-10T09:08:00+05:30"
        pack["preopen"]["as_of_ist"] = "2026-11-10T09:08:00+05:30"
        payload = build_premarket(pack)
        self.assertFalse(_one(payload, "preopen", "NIFTY")["ok"])

    def test_flows_keep_the_session_date_and_refuse_spy(self):
        pack = _load("flows.json")
        pack["deals"].append(
            {"kind": "bulk", "symbol": "SPY", "exchange": "NSE", "qty": 1, "price": 1, "client": "nope"}
        )
        payload = read_flows(pack)
        self.assertEqual(_one(payload, "fii_cash_net")["freshness"], "previous_session")
        self.assertTrue(_one(payload, "deal_qty", "RELIANCE")["ok"])
        spy = [row for row in payload["items"] if row["symbol"] == "SPY"]
        self.assertTrue(spy)
        self.assertFalse(spy[0]["ok"])

    def test_breadth_scores_only_fields_present(self):
        payload = read_breadth(_load("breadth.json"))
        self.assertEqual(_one(payload, "advance_decline_ratio")["value"], 1.5)
        self.assertEqual(_one(payload, "concentration")["value"], "narrow")
        self.assertFalse(_one(payload, "new_highs")["ok"])
        refused = read_breadth({"exchange": "MCX", "session_date": "2026-11-05", "source": "fixture:x"})
        self.assertEqual(refused["error"], "outside_universe")

    def test_rotation_windows(self):
        payload = read_rotation(_load("rotation.json"))
        self.assertEqual(_one(payload, "rs_5d_pct", "NIFTYIT")["value"], 7.0)
        self.assertEqual(_one(payload, "rs_5d_pct", "NIFTYAUTO")["value"], -13.0)
        self.assertFalse(_one(payload, "rs_20d_pct", "NIFTYIT")["ok"])
        self.assertFalse(_one(payload, "rs_60d_pct", "NIFTYIT")["ok"])

    def test_options_chain_does_not_invent_a_lot_or_a_strategy(self):
        payload = read_options(_load("options_nifty.json"))
        self.assertEqual(_one(payload, "put_call_ratio")["value"], 1.2)
        self.assertEqual(_one(payload, "days_to_expiry")["value"], 4)
        self.assertEqual(_one(payload, "call_oi_change_around_spot")["value"], 15)
        self.assertEqual(_one(payload, "nearest_expiry")["value"], "2026-11-09")
        self.assertNotIn("recommendation", {row["field"] for row in payload["items"]})
        pack = _load("options_nifty.json")
        del pack["lot_size"]
        blank = read_options(pack)
        self.assertFalse(_one(blank, "lot_size")["ok"])

    def test_levels_use_the_completed_session_and_the_opening_range(self):
        payload = read_levels(_load("levels_reliance.json"))
        self.assertEqual(_one(payload, "prev_high")["value"], 114)
        self.assertEqual(_one(payload, "week_high")["value"], 114)
        self.assertEqual(_one(payload, "week_low")["value"], 104)
        self.assertEqual(_one(payload, "cpr_pivot")["value"], round((114 + 109 + 112) / 3, 4))
        self.assertEqual(_one(payload, "opening_range_high")["value"], 113.0)
        self.assertEqual(_one(payload, "opening_range_low")["value"], 111.6)

    def test_desk_routes_one_skill_and_stops_when_two_match(self):
        self.assertEqual(route_request("read the tape on RELIANCE")["skill"], "tape-reading")
        self.assertEqual(route_request("fii dii cash yesterday")["skill"], "institutional-flows")
        self.assertEqual(route_request("put call ratio on nifty")["skill"], "options-positioning")
        vague = route_request("what is india vix")
        self.assertFalse(vague["ok"])
        self.assertEqual(vague["error"], "ambiguous")
        self.assertIn("premarket-brief", vague["candidates"])
        self.assertIn("options-positioning", vague["candidates"])
        self.assertEqual(route_request("hello there")["error"], "no_route")


class Phase3Tests(unittest.TestCase):
    def test_fundamentals_follow_the_fiscal_year(self):
        payload = read_fundamentals(_load("fundamentals_reliance.json"))
        self.assertEqual(_one(payload, "pe")["value"], 25.0)
        self.assertEqual(_one(payload, "roe_pct")["value"], 20.0)
        self.assertEqual(_one(payload, "pledge_pct")["value"], 1.2)
        self.assertEqual(_one(payload, "shareholding_sum_pct")["value"], 100.0)
        pack = _load("fundamentals_reliance.json")
        pack["quarters"][0]["period"] = "Q1 FY2026"
        mismatched = read_fundamentals(pack)
        self.assertFalse(_one(mismatched, "period")["ok"])
        self.assertFalse(_one(mismatched, "pe")["ok"])

    def test_concall_leaves_a_missing_decline_blank(self):
        payload = read_concall(_load("concall_reliance.json"))
        self.assertTrue(_one(payload, "declined")["ok"])
        pack = _load("concall_reliance.json")
        pack["excerpts"] = [row for row in pack["excerpts"] if row["topic"] != "declined"]
        blank = read_concall(pack)
        declined = _one(blank, "declined")
        self.assertFalse(declined["ok"])
        self.assertIsNone(declined["value"])
        path = fixtures_dir() / "reliance_concall_ok.md"
        self.assertTrue(check_brief(path, "concall")["ok"])

    def test_actions_keep_the_ex_date_and_drop_an_unknown_kind(self):
        payload = read_actions(_load("actions_reliance.json"))
        self.assertEqual(_one(payload, "ex_date")["value"], "2026-11-14")
        self.assertIn("dividend", {row["value"] for row in payload["items"] if row["field"] == "corporate_action"})
        pack = _load("actions_reliance.json")
        pack["actions"].append({"kind": "merger", "headline": "Scheme", "source": "fixture:merger"})
        refused = read_actions(pack)
        self.assertTrue(any(not row["ok"] and row["field"] == "corporate_action" for row in refused["items"]))

    def test_results_calendar_is_the_watchlist_from_as_of(self):
        payload = read_results(_load("results_calendar.json"))
        self.assertEqual(_one(payload, "results_meeting", "RELIANCE")["value"], "2026-11-14")
        self.assertFalse(_one(payload, "results_meeting", "TCS")["ok"])
        self.assertNotIn("INFY", {row["symbol"] for row in payload["items"]})
        pack = _load("results_calendar.json")
        pack["watchlist"].append("TSLA")
        refused = read_results(pack)
        tsla = [row for row in refused["items"] if row["symbol"] == "TSLA"]
        self.assertTrue(tsla)
        self.assertFalse(tsla[0]["ok"])


class SkillLayoutTests(unittest.TestCase):
    def test_phase1_skills_exist_and_match_their_directory(self):
        root = ROOT / ".claude" / "skills"
        expected = {
            "market-core",
            "surveillance-check",
            "market-research",
            "market-analysis",
            "swot-analysis",
            "tape-reading",
            "premarket-brief",
            "institutional-flows",
            "market-breadth",
            "sector-rotation",
            "options-positioning",
            "levels-plan",
            "indian-desk",
            "fundamentals",
            "concall-reader",
            "corporate-actions",
            "results-calendar",
            "trade-plan",
            "position-size",
            "risk-gate",
            "trade-journal",
            "scanner",
            "backtest-india",
            "paper-ticket",
            "opening-range-break",
            "previous-day-break",
            "vwap-hold",
            "delivery-rs",
            "sector-leader",
            "post-result",
            "morning-chain",
            "journal-review",
            "official-files",
            "mandate",
            "thesis-memo",
            "short-case",
            "book-risk",
            "pair-note",
            "ic-note",
        }
        for name in expected:
            text = (root / name / "SKILL.md").read_text(encoding="utf-8")
            self.assertLess(len(text.splitlines()), 500, name)
            self.assertIn(f"name: {name}", text.split("---")[1])


class Phase4Tests(unittest.TestCase):
    def test_plan_r_and_a_wrong_side(self):
        payload = read_plan(_load("plan_reliance.json"))
        self.assertEqual(payload["plan_status"], "ready")
        self.assertEqual(_one(payload, "r_multiple")["value"], 2.0)
        pack = _load("plan_reliance.json")
        pack["invalidation"] = 120
        invalid = read_plan(pack)
        self.assertEqual(invalid["plan_status"], "invalid")
        self.assertFalse(_one(invalid, "r_multiple")["ok"])
        pack["side"] = "buy"
        incomplete = read_plan(pack)
        self.assertEqual(incomplete["plan_status"], "incomplete")
        self.assertFalse(_one(incomplete, "r_multiple")["ok"])

    def test_size_floors_to_the_lot_and_reads_the_charge_sheet(self):
        payload = size_position(_load("size_reliance.json"))
        self.assertEqual(_one(payload, "quantity")["value"], 333)
        self.assertEqual(_one(payload, "stt_inr")["value"], 9.32)
        self.assertFalse(_one(payload, "stamp_inr")["ok"])
        self.assertIsNone(_one(payload, "stamp_inr")["value"])
        self.assertFalse(_one(payload, "gst_inr")["ok"])
        pack = _load("size_reliance.json")
        pack["lot_size"] = 10
        pack["brokerage_inr"] = 20
        sized = size_position(pack)
        self.assertEqual(_one(sized, "quantity")["value"], 330)
        self.assertEqual(_one(sized, "exchange_txn_inr")["value"], 2.27)
        self.assertEqual(_one(sized, "gst_inr")["value"], 4.01)
        blocked = _load("size_reliance.json")
        blocked["horizon"] = "futures"
        blocked["fo_ban"] = True
        refused = size_position(blocked)
        self.assertFalse(_one(refused, "quantity")["ok"])
        self.assertIsNone(_one(refused, "quantity")["value"])
        stale = _load("size_reliance.json")
        stale["as_of"] = "2027-06-01"
        blank = size_position(stale)
        self.assertEqual(_one(blank, "quantity")["value"], 333)
        self.assertFalse(_one(blank, "stt_inr")["ok"])

    def test_gate_pass_and_block(self):
        passed = assess_gate(_load("gate_pass.json"))
        self.assertTrue(passed["ok"])
        self.assertEqual(passed["gate"], "PASS")
        self.assertEqual(passed["reasons"], [])
        cash_expiry = _load("gate_pass.json")
        cash_expiry["expiry_day"] = True
        self.assertEqual(assess_gate(cash_expiry)["gate"], "PASS")
        blocked = {
            "symbol": "RELIANCE",
            "exchange": "NSE",
            "source": "fixture:gate",
            "horizon": "futures",
            "clearance": "blocked",
            "fo_ban": True,
            "near_circuit": True,
            "results_day": True,
            "expiry_day": True,
            "r_multiple": 0.5,
            "min_r": 2,
            "daily_loss_inr": 5000,
            "daily_loss_limit_inr": 5000,
            "planned_trades": 3,
            "max_planned_trades": 3,
            "data_as_of_ist": "2026-11-06T09:00:00+05:30",
            "now_ist": "2026-11-06T12:00:00+05:30",
            "max_age_minutes": 30,
            "costs_as_of": "2027-06-01",
        }
        decision = assess_gate(blocked)
        self.assertTrue(decision["ok"])
        self.assertEqual(decision["gate"], "BLOCK")
        text = " ".join(decision["reasons"])
        for phrase in (
            "clearance is blocked",
            "F&O ban",
            "near the circuit",
            "results day",
            "expires in the session",
            "below the minimum",
            "Daily loss",
            "plan cap",
            "minutes",
            "stale",
        ):
            self.assertIn(phrase, text)

    def test_journal_is_append_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "journal.jsonl"
            pack = {
                "symbol": "RELIANCE",
                "exchange": "NSE",
                "id": "RELIANCE-test",
                "setup": "opening_range_break",
                "planned_risk_inr": 1000,
                "source": "fixture:journal",
                "horizon": "intraday_cash",
            }
            written = add_plan(path, pack, at="2026-11-06T09:20:00+05:30")
            self.assertTrue(written["ok"])
            first = path.read_text(encoding="utf-8")
            later = add_outcome(path, pack["id"], "target_hit", at="2026-11-06T15:30:00+05:30", source="fixture:journal")
            self.assertTrue(later["ok"])
            text = path.read_text(encoding="utf-8")
            self.assertTrue(text.startswith(first))
            self.assertEqual(text.splitlines()[0], first.splitlines()[0])
            self.assertEqual(later["entries"][0]["outcome"], "target_hit")
            before = path.read_bytes()
            unknown = add_outcome(path, "missing", "stopped")
            self.assertFalse(unknown["ok"])
            self.assertEqual(unknown["error"], "unknown_id")
            rejected = add_outcome(path, pack["id"], "buy")
            self.assertFalse(rejected["ok"])
            self.assertEqual(rejected["error"], "bad_input")
            self.assertEqual(path.read_bytes(), before)
            sample = show_journal(fixtures_dir() / "journal_sample.jsonl")
            self.assertEqual(sample["entries"][0]["outcome"], "open")
            self.assertEqual(sample["entries"][0]["setup"], "opening_range_break")


class Phase5Tests(unittest.TestCase):
    def test_scan_excludes_ban_and_keeps_the_named_hits(self):
        payload = scan_list(_load("scan_list.json"))
        reliance = {
            row["value"]
            for row in payload["items"]
            if row["symbol"] == "RELIANCE" and row["field"] == "scan_hit" and row["ok"]
        }
        self.assertEqual(reliance, {"opening_range_break_up", "high_delivery"})
        self.assertEqual(_one(payload, "scan_excluded", "SAIL")["value"], "fo_ban")
        self.assertEqual(_one(payload, "scan_excluded", "INFY")["value"], "trade_for_trade")
        self.assertFalse(any(row["symbol"] == "SAIL" and row["field"] == "scan_hit" for row in payload["items"]))
        spy = [row for row in payload["items"] if row["symbol"] == "SPY"]
        self.assertEqual(len(spy), 1)
        self.assertFalse(spy[0]["ok"])
        self.assertEqual(spy[0]["field"], "scan_hit")
        self.assertIsNone(spy[0]["value"])
        self.assertNotIn("TCS", {row["symbol"] for row in payload["items"]})

    def test_backtest_requires_stt_and_calls_out_expiry_week(self):
        demo = run_backtest(_load("backtest_reliance.json"))
        self.assertEqual(_one(demo, "net_pnl_inr")["value"], 39.71)
        self.assertEqual(_one(demo, "stt_inr")["value"], 0.29)
        self.assertEqual(_one(demo, "slippage_inr")["value"], 20.0)
        self.assertTrue(_one(demo, "expiry_week")["value"])
        ignored = _load("backtest_reliance.json")
        ignored["include_stt"] = False
        refused = run_backtest(ignored)
        self.assertFalse(refused["ok"])
        self.assertEqual(refused["error"], "stt_required")
        self.assertFalse(any(row["field"] == "net_pnl_inr" and row["ok"] for row in refused["items"]))
        bare = _load("backtest_reliance.json")
        del bare["slippage_ticks"]
        self.assertFalse(_one(run_backtest(bare), "slippage_inr")["ok"])
        stock = _load("backtest_reliance.json")
        del stock["trades"][0]["expiry_date"]
        week = _one(run_backtest(stock), "expiry_week")
        self.assertFalse(week["value"])
        self.assertIn("expiry_date", week["detail"])

        def nifty(day):
            return run_backtest(
                {
                    "symbol": "NIFTY",
                    "exchange": "NSE",
                    "source": "fixture:backtest",
                    "horizon": "futures",
                    "include_stt": True,
                    "slippage_ticks": 0,
                    "tick_size": 0.05,
                    "trades": [
                        {
                            "side": "long",
                            "entry": 24000,
                            "exit": 24100,
                            "qty": 1,
                            "exit_time": f"{day}T15:20:00+05:30",
                        }
                    ],
                }
            )

        on_expiry = nifty("2026-11-09")
        self.assertTrue(_one(on_expiry, "expiry_week")["value"])
        self.assertEqual(_one(on_expiry, "net_pnl_inr")["value"], 87.95)
        self.assertFalse(_one(nifty("2026-11-06"), "expiry_week")["value"])
        before_review = nifty("2026-11-02")
        self.assertFalse(before_review["ok"])
        self.assertFalse(any(row["field"] == "net_pnl_inr" and row["ok"] for row in before_review["items"]))

    def test_ticket_stores_yes_only_when_the_gate_passed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "journal.jsonl"
            add_plan(
                path,
                {
                    "symbol": "RELIANCE",
                    "exchange": "NSE",
                    "id": "RELIANCE-test",
                    "setup": "opening_range_break",
                    "planned_risk_inr": 1000,
                    "source": "fixture:journal",
                },
                at="2026-11-06T09:20:00+05:30",
            )
            base = _load("ticket_reliance.json")
            base["id"] = "RELIANCE-test"
            base["journal_path"] = str(path)
            before = path.read_bytes()
            draft = build_ticket(base)
            self.assertEqual(draft["ticket_status"], "draft")
            self.assertFalse(draft["human_yes_stored"])
            self.assertEqual(path.read_bytes(), before)
            blocked = dict(base)
            blocked["gate"] = "BLOCK"
            blocked["human_yes"] = True
            refused = build_ticket(blocked)
            self.assertEqual(refused["ticket_status"], "blocked")
            self.assertFalse(any(row["field"] == "ticket" and row["ok"] for row in refused["items"]))
            self.assertEqual(path.read_bytes(), before)
            ready_pack = dict(base)
            ready_pack["human_yes"] = True
            ready = build_ticket(ready_pack)
            self.assertEqual(ready["ticket_status"], "ready")
            self.assertTrue(ready["human_yes_stored"])
            self.assertIn("Nothing was sent to a broker", _one(ready, "ticket")["detail"])
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(json.loads(lines[0])["event"], "plan")
            self.assertEqual(json.loads(lines[-1])["event"], "human_yes")
            self.assertFalse(Path(tmp).joinpath("missing.jsonl").exists())
            orphan = build_ticket({**ready_pack, "id": "missing", "journal_path": str(Path(tmp) / "missing.jsonl")})
            self.assertEqual(orphan["ticket_status"], "draft")
            self.assertFalse(orphan["human_yes_stored"])
            self.assertFalse((Path(tmp) / "missing.jsonl").exists())

    def test_desk_routes_the_new_jobs_and_still_refuses_an_order(self):
        self.assertEqual(route_request("position size for delivery")["skill"], "position-size")
        self.assertEqual(route_request("paper ticket for RELIANCE")["skill"], "paper-ticket")
        self.assertEqual(route_request("backtest with stt")["skill"], "backtest-india")
        self.assertEqual(route_request("scan for opening range breaks")["skill"], "scanner")
        order = route_request("place an order")
        self.assertFalse(order["ok"])
        self.assertEqual(order["error"], "no_route")
        vague = route_request("what is india vix")
        self.assertFalse(vague["ok"])
        self.assertEqual(vague["error"], "ambiguous")


class Phase6Tests(unittest.TestCase):
    def test_setup_cards_pass_and_fail(self):
        orb = opening_range_break(_load("setup_orb.json"))
        self.assertEqual(orb["plan_status"], "ready")
        self.assertEqual(orb["setup"], "opening_range_break")
        self.assertEqual(_one(orb, "entry")["value"], 114)
        self.assertEqual(_one(orb, "invalidation")["value"], 111)
        self.assertEqual(_one(orb, "target")["value"], 120)
        self.assertEqual(_one(orb, "r_multiple")["value"], 2.0)
        inside = dict(_load("setup_orb.json"))
        inside["last"] = 112
        self.assertEqual(opening_range_break(inside)["plan_status"], "invalid")
        be = dict(_load("setup_orb.json"))
        be["series"] = "BE"
        self.assertEqual(opening_range_break(be)["plan_status"], "blocked")

        pdh = previous_day_break(_load("setup_pdh.json"))
        self.assertEqual(pdh["plan_status"], "ready")
        self.assertEqual(_one(pdh, "entry")["value"], 116)
        self.assertEqual(_one(pdh, "invalidation")["value"], 114)
        self.assertEqual(_one(pdh, "target")["value"], 120)
        self.assertEqual(_one(pdh, "r_multiple")["value"], 2.0)
        quiet = dict(_load("setup_pdh.json"))
        quiet["last"] = 112
        self.assertEqual(previous_day_break(quiet)["plan_status"], "invalid")

        held = vwap_hold(_load("setup_vwap.json"))
        self.assertEqual(held["plan_status"], "ready")
        self.assertEqual(held["setup"], "vwap_hold")
        self.assertEqual(_one(held, "entry")["value"], 114)
        self.assertEqual(_one(held, "invalidation")["value"], 112)
        self.assertEqual(_one(held, "target")["value"], 118)
        self.assertEqual(_one(held, "r_multiple")["value"], 2.0)
        under = dict(_load("setup_vwap.json"))
        under["last"] = 112
        self.assertEqual(vwap_hold(under)["plan_status"], "invalid")

        delivered = delivery_rs(_load("setup_delivery.json"))
        self.assertEqual(delivered["plan_status"], "ready")
        self.assertEqual(delivered["setup"], "delivery_rs")
        self.assertEqual(_one(delivered, "horizon")["value"], "delivery")
        self.assertEqual(_one(delivered, "entry")["value"], 112)
        self.assertEqual(_one(delivered, "invalidation")["value"], 109)
        self.assertEqual(_one(delivered, "target")["value"], 118)
        self.assertEqual(_one(delivered, "r_multiple")["value"], 2.0)
        thin = dict(_load("setup_delivery.json"))
        thin["delivery_pct"] = 40
        self.assertEqual(delivery_rs(thin)["plan_status"], "invalid")
        bare = dict(_load("setup_delivery.json"))
        bare.pop("min_delivery_pct")
        self.assertNotEqual(delivery_rs(bare)["plan_status"], "ready")

        leader = sector_leader(_load("setup_sector.json"))
        self.assertEqual(leader["plan_status"], "ready")
        self.assertEqual(leader["setup"], "sector_leader")
        self.assertEqual(_one(leader, "r_multiple")["value"], 2.0)
        other = dict(_load("setup_sector.json"))
        other["sector"] = "NIFTYAUTO"
        self.assertEqual(sector_leader(other)["plan_status"], "invalid")

        gap = post_result(_load("setup_post.json"))
        self.assertEqual(gap["plan_status"], "ready")
        self.assertEqual(gap["setup"], "post_result")
        self.assertEqual(_one(gap, "side")["value"], "long")
        self.assertEqual(_one(gap, "entry")["value"], 104)
        self.assertEqual(_one(gap, "invalidation")["value"], 100)
        self.assertEqual(_one(gap, "target")["value"], 112)
        self.assertEqual(_one(gap, "r_multiple")["value"], 2.0)
        self.assertFalse(_one(gap, "ex_date")["ok"])
        same_day = dict(_load("setup_post.json"))
        same_day["session_date"] = same_day["results_date"]
        self.assertEqual(post_result(same_day)["plan_status"], "blocked")

    def test_contract_identity_keeps_the_cash_demo_ready(self):
        cash = read_plan(_load("plan_reliance.json"))
        self.assertEqual(cash["plan_status"], "ready")
        futures = _load("plan_reliance.json")
        futures["horizon"] = "futures"
        self.assertEqual(read_plan(futures)["plan_status"], "incomplete")
        options = _load("plan_reliance.json")
        options["horizon"] = "options"
        options["expiry_date"] = "2026-11-24"
        options["lot_size"] = 250
        self.assertEqual(read_plan(options)["plan_status"], "incomplete")
        self.assertFalse(_one(read_plan(options), "option")["ok"])

    def test_morning_pass_skips_a_ticket_and_block_skips_it_too(self):
        passed = run_morning(_load("morning.json"))
        self.assertTrue(passed["ok"])
        self.assertEqual(passed["chain_status"], "gate_pass")
        self.assertFalse(any(row["field"] == "ticket" and row["ok"] for row in passed["items"]))
        blocked = _load("morning.json")
        blocked["gate"]["fo_ban"] = True
        blocked["gate"]["horizon"] = "futures"
        stopped = run_morning(blocked)
        self.assertEqual(stopped["chain_status"], "BLOCK")
        self.assertFalse(any(row["field"] == "ticket" and row["ok"] for row in stopped["items"]))

    def test_journal_review_numbers_and_open_risk(self):
        path = fixtures_dir() / "journal_review.jsonl"
        payload = review_journal(path, as_of="2026-11-06")
        self.assertEqual(_one(payload, "hit_rate")["value"], 0.5)
        self.assertEqual(_one(payload, "avg_r")["value"], 0.5)
        self.assertEqual(_one(payload, "net_after_stt_inr")["value"], 794.8)
        self.assertEqual(_one(payload, "open_risk_inr")["value"], 1000)
        self.assertEqual(open_risk_inr(path), 1000)
        nets = sorted(row["value"] for row in payload["items"] if row["field"] == "trade_net_inr" and row["ok"])
        self.assertEqual(nets, [-202.45, 997.25])

    def test_outcome_stores_realized_r_and_demo_does_not_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "journal.jsonl"
            add_plan(
                path,
                {
                    "symbol": "RELIANCE",
                    "exchange": "NSE",
                    "id": "ORB-test",
                    "setup": "opening_range_break",
                    "planned_risk_inr": 1000,
                    "source": "fixture:journal",
                    "entry": 100,
                    "qty": 100,
                    "side": "long",
                },
                at="2026-11-06T09:20:00+05:30",
            )
            add_outcome(
                path,
                "ORB-test",
                "target_hit",
                at="2026-11-06T15:20:00+05:30",
                source="fixture:journal",
                realized_r=2,
                exit_price=110,
            )
            row = show_journal(path)["entries"][0]
            self.assertEqual(row["realized_r"], 2)
            self.assertEqual(row["exit_price"], 110)
            before = path.read_bytes()
            with redirect_stdout(io.StringIO()):
                code = main(["journal-outcome", "--demo", "--id", "ORB-test", "--outcome", "stopped", "--path", str(path)])
            self.assertEqual(code, 0)
            self.assertEqual(path.read_bytes(), before)

    def test_gate_optional_checks_skip_when_absent_and_block_when_set(self):
        passed = assess_gate(_load("gate_pass.json"))
        self.assertEqual(passed["gate"], "PASS")
        self.assertEqual(passed["reasons"], [])
        for key, value in (
            ("muhurat", True),
            ("ex_date_today", True),
            ("record_date_today", True),
            ("board_meeting_today", True),
        ):
            pack = _load("gate_pass.json")
            pack[key] = value
            decision = assess_gate(pack)
            self.assertEqual(decision["gate"], "BLOCK", key)
        distance = _load("gate_pass.json")
        distance["circuit_distance_inr"] = 1
        distance["min_circuit_distance_inr"] = 5
        self.assertEqual(assess_gate(distance)["gate"], "BLOCK")
        risk = _load("gate_pass.json")
        risk["open_risk_inr"] = 5000
        self.assertEqual(assess_gate(risk)["gate"], "BLOCK")

    def test_series_report_does_not_rewrite_the_book(self):
        book = ROOT / "data" / "symbols.json"
        before = book.read_bytes()
        report = series_report(fixtures_dir() / "series_sample.csv")
        self.assertEqual(book.read_bytes(), before)
        self.assertEqual(report["verified"], 1)
        self.assertEqual(report["unverified"], ["ZYDUSLIFE"])
        self.assertEqual(report["refused"][0]["symbol"], "SPY")

    def test_official_fixtures_parse_and_a_bad_url_stays_blank(self):
        session = "2026-11-06"
        cash = parse_official("cash_bhav", fixtures_dir() / "official_cash.csv", session, "fixture:official_cash.csv")
        self.assertEqual(_one(cash, "close", "RELIANCE")["value"], 112)
        self.assertEqual(_one(cash, "delivery_pct", "RELIANCE")["value"], 62)
        ban = parse_official("ban", fixtures_dir() / "official_ban.csv", session, "fixture:official_ban.csv")
        self.assertIs(True, _one(ban, "fo_ban", "SAIL")["value"])
        contract = parse_official("contract", fixtures_dir() / "official_contract.csv", session, "fixture:official_contract.csv")
        self.assertEqual(_one(contract, "lot_size", "NIFTY")["value"], 65)
        self.assertEqual(_one(contract, "tick_size", "NIFTY")["value"], 0.05)
        failed = fetch_official("cash_bhav", session, url="not-a-url")
        self.assertFalse(failed["ok"])
        self.assertEqual(failed["error"], "no_evidence")
        self.assertFalse(any(row["ok"] for row in failed["items"]))

    def test_backtest_drawdown_and_exchange_charge_stay_beside_the_demo_net(self):
        demo = run_backtest(_load("backtest_reliance.json"))
        self.assertEqual(_one(demo, "net_pnl_inr")["value"], 39.71)
        self.assertEqual(_one(demo, "stt_inr")["value"], 0.29)
        self.assertEqual(_one(demo, "slippage_inr")["value"], 20.0)
        self.assertEqual(_one(demo, "exchange_txn_inr")["value"], 0.07)
        self.assertEqual(_one(demo, "max_drawdown_inr")["value"], 0)
        self.assertEqual(_one(demo, "horizon_net_pnl_inr")["value"], 39.71)
        loser = _load("backtest_reliance.json")
        loser["trades"].append(
            {
                "side": "long",
                "entry": 118,
                "exit": 100,
                "qty": 10,
                "exit_time": "2026-11-24T15:25:00+05:30",
                "expiry_date": "2026-11-24",
            }
        )
        drawn = run_backtest(loser)
        self.assertGreater(_one(drawn, "max_drawdown_inr")["value"], 0)
        bse = _load("backtest_reliance.json")
        bse["exchange"] = "BSE"
        blank = run_backtest(bse)
        self.assertEqual(_one(blank, "net_pnl_inr")["value"], 39.71)
        self.assertFalse(_one(blank, "exchange_txn_inr")["ok"])

    def test_next_session_after_the_friday_result_is_muhurat(self):
        self.assertEqual(next_trading_day("2026-11-06").isoformat(), "2026-11-08")

    def test_desk_keeps_the_scan_sentence_and_routes_the_new_jobs(self):
        self.assertEqual(route_request("scan for opening range breaks")["skill"], "scanner")
        self.assertEqual(route_request("orb setup")["skill"], "opening-range-break")
        self.assertEqual(route_request("opening range strategy")["skill"], "opening-range-break")
        self.assertEqual(route_request("vwap on reliance")["skill"], "tape-reading")
        self.assertEqual(route_request("vwap hold")["skill"], "vwap-hold")
        self.assertEqual(route_request("delivery and relative strength")["skill"], "delivery-rs")
        self.assertEqual(route_request("journal")["skill"], "trade-journal")
        self.assertEqual(route_request("journal review")["skill"], "journal-review")
        self.assertEqual(route_request("previous day break")["skill"], "previous-day-break")
        self.assertEqual(route_request("sector leader")["skill"], "sector-leader")
        self.assertEqual(route_request("post result")["skill"], "post-result")
        self.assertEqual(route_request("morning chain")["skill"], "morning-chain")
        self.assertEqual(route_request("parse the bhav copy")["skill"], "official-files")
        self.assertEqual(route_request("trading mandate")["skill"], "mandate")
        self.assertEqual(route_request("investment thesis")["skill"], "thesis-memo")
        self.assertEqual(route_request("short case")["skill"], "short-case")
        self.assertEqual(route_request("book risk")["skill"], "book-risk")
        self.assertEqual(route_request("pair trade")["skill"], "pair-note")
        self.assertEqual(route_request("investment committee")["skill"], "ic-note")
        self.assertEqual(route_request("investment committee")["command"], "none")
        self.assertEqual(route_request("risk gate")["skill"], "risk-gate")
        self.assertEqual(route_request("place an order")["error"], "no_route")
        vague = route_request("what is india vix")
        self.assertEqual(vague["error"], "ambiguous")


if __name__ == "__main__":
    unittest.main()
