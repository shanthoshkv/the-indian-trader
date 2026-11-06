import io
import unittest
from contextlib import redirect_stdout
from datetime import date, datetime

import _path  # noqa: F401

from indian_market.analysis import analyze, oi_quadrant
from indian_market.briefs import check_brief
from indian_market.calendar_in import IST, is_trading_day, session_state
from indian_market.cli import main
from indian_market.costs import review_status
from indian_market.expiry import next_expiry
from indian_market.paths import fixtures_dir, repo_root
from indian_market.surveillance import clear
from indian_market.tape import read_tape
from indian_market.universe import resolve

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
        }
        for name in expected:
            text = (root / name / "SKILL.md").read_text(encoding="utf-8")
            self.assertLess(len(text.splitlines()), 500, name)
            self.assertIn(f"name: {name}", text.split("---")[1])


if __name__ == "__main__":
    unittest.main()
