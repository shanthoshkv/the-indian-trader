# The Indian Trader

Claude Code skills for people who trade **only on the NSE and the BSE**.

The pack is a research desk, not a broker and not a tip service. Every price, delivery figure, and open-interest label has to come from a command in this repo, with a source and a session date. If the command has no figure, the note leaves the field blank. Nothing here places an order.

This is not a SEBI-registered research analyst, and it is not investment advice.

## What you can ask today

Phase 1 is shipped. Open this repo in Claude Code and the skills in `.claude/skills/` load on their own.

| Skill | Ask it |
| --- | --- |
| `market-core` | Is the market open? When is Nifty expiry? What is the STT snapshot? Which exchange is this symbol? |
| `surveillance-check` | Is this name in F&O ban, ASM, GSM, ESM, or trade-for-trade? |
| `market-research` | What does this listed company do, and what did the filings just say? |
| `market-analysis` | Where is price, delivery, relative strength versus Nifty or Sensex, and futures buildup? |
| `swot-analysis` | SWOT, where every bullet needs a filing or an exchange source |
| `tape-reading` | Opening range, VWAP, previous-day high and low, on bars you actually have |

A US ticker, a crypto name, or an MCX commodity is refused. A name listed on both exchanges defaults to NSE EQ. Say BSE, pass `RELIANCE.BO`, or pass the 6-digit scrip code when you want the BSE listing.

## Install

Python 3.11 or newer. The core uses the standard library only.

```powershell
git clone https://github.com/shanthoshkv/the-indian-trader.git
cd the-indian-trader
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -v
```

Skills are already in `.claude/skills/` for sessions opened in this repo. To use them in every project on this machine, copy those folders to `%USERPROFILE%\.claude\skills\`.

On macOS or Linux, set the path with `export PYTHONPATH=src` and run `python3` if `python` is not 3.11+.

## Commands

```powershell
$env:PYTHONPATH = "src"
python -m indian_market.cli resolve RELIANCE
python -m indian_market.cli resolve RELIANCE --exchange BSE
python -m indian_market.cli session
python -m indian_market.cli expiry NIFTY --on 2026-11-06
python -m indian_market.cli expiry BANKNIFTY --on 2026-11-06
python -m indian_market.cli costs
python -m indian_market.cli analyze --demo
python -m indian_market.cli tape --demo
python -m indian_market.cli surveillance --demo --segment fo
python -m indian_market.cli check-brief data\fixtures\reliance_research_ok.md --kind research
```

`--demo` replays recorded samples in `data/fixtures/`. Those rows are marked `fixture`. They are not a live quote.

`analyze`, `tape`, and `surveillance` refuse to run with no file. Pass `--fixture path\to\pack.json`, or `--demo`. The JSON shapes are in each skill's `SKILL.md`.

Exit `0` means the evidence is usable. Exit `2` means the symbol is outside NSE and BSE, or the evidence file was not provided. That is a finished answer. The model is not supposed to fill the gap from memory.

## How a number is allowed to appear

```json
{
  "ok": true,
  "symbol": "RELIANCE",
  "exchange": "NSE",
  "series": "EQ",
  "field": "close",
  "value": 108.0,
  "unit": "INR",
  "session_date": "2026-11-05",
  "as_of_ist": "2026-11-05T18:10:00+05:30",
  "source": "fixture:nse-cm-bhavcopy",
  "freshness": "fixture"
}
```

`freshness` is one of `live_snapshot`, `previous_session`, `delayed_vendor`, `filing`, `fixture`, or `unavailable`.

FII, DII, and delivery percent during the session are previous-session figures. The cash bhavcopy is published after the close. Yahoo `.NS` / `.BO` daily bars are allowed only as delayed OHLC when no bhavcopy is available. They are not a source for open interest, delivery, ban status, or corporate actions.

Research and SWOT notes are checked with `check-brief`. A bullet without `source:` fails. A buy or sell verdict fails. Sources must be an `http` URL, an NSE or BSE filing id, or a `fixture:` label.

## Market rules encoded in the core

These live in one place, `market-core`, and in `data/holidays.json` and `data/costs.json`. Skills point at that core. They do not each restate the weekday.

| Rule | What this pack uses |
| --- | --- |
| Cash session | 09:15–15:30 IST |
| Pre-open | 09:00–09:05 limit and market, 09:05–09:10 limit only, then match and buffer to 09:15. Market orders after 09:05 are not part of this schedule. Revised from 7 September 2026. |
| Weekly expiry | Nifty on Tuesday (NSE). Sensex on Thursday (BSE). A holiday moves that expiry to the previous trading session. |
| No weekly | Bank Nifty, Fin Nifty, Midcap Select, and stock futures and options. Monthly only. |
| Monthly expiry | Last Tuesday on NSE. Last Thursday on BSE (Sensex, Bankex). |
| Muhurat 2026 | Sunday 8 November, equity 14:20–15:30 IST, pre-open from 14:05. NSE/CMTR/76941. |
| Holidays | NSE circular NSE/CMTR/71775 dated 12 December 2025. 15 January 2026 is on the BSE list and is not in that NSE extract, so the calendar treats it as BSE-only. |
| Charges | `data/costs.json`, with `effective_from` and `last_reviewed`. The sheet fails its own check 180 days after review. Stamp duty has no single national rate. |

The week of 6 November 2026 is the worked example in the tests: Nifty's Tuesday expiry falls on Diwali Balipratipada, so the weekly expiry is Monday 9 November. The monthly, including Bank Nifty, is Monday 23 November because 24 November is a holiday.

Lot size and tick size are not hardcoded for a trade. When a security file is absent, the April 2025 cash and stock-futures tick schedule is documented in `market-core` as a fallback, and the security file wins when a series differs.

## Roadmap

Status is the state of this repository, not a promise of a date.

### Phase 0 — Core

**Shipped.** Symbol resolver, IST session clock, holiday list, expiry calendar, dated charge sheet, evidence JSON, and offline tests. The library is `src/indian_market`. The skill is `market-core`.

### Phase 1 — The desk

**Shipped.** The four skills the project was started for, plus the check that has to run before trade language.

| Skill | Job |
| --- | --- |
| `market-research` | Business, last quarter, shareholding, announcements, listed peers, open questions. Citations only. |
| `market-analysis` | Close, change, delivery percent, 5- and 20-session return, relative strength, futures price-OI quadrant (`long_buildup`, `short_buildup`, `long_unwinding`, `short_covering`). |
| `swot-analysis` | Strengths, weaknesses, opportunities, threats, and what would flip the SWOT. Each bullet cites a filing. |
| `tape-reading` | Session mode: opening range 09:15–09:30 IST, VWAP from the bars supplied, previous-day high and low, prior delivery percent. Print mode only when a time-and-sales feed is actually in the file. |
| `surveillance-check` | Series, price band, ASM, GSM, ESM, trade-for-trade, F&O ban. Cash of a banned name is `caution`. Fresh F&O on a banned name is `blocked`. |

Live downloads from nseindia.com and bseindia.com are **not** in this phase. You pass a JSON file built from an exchange download, or you use `--demo`.

### Phase 2 — The session around the desk

**Not started.** One skill per job. A router that does not reimplement the others.

| Skill | Job |
| --- | --- |
| `premarket-brief` | Previous close, pre-open once 09:00 IST has printed, overnight announcements, last completed FII/DII session with that date attached, India VIX previous close, this week's Tuesday Nifty and Thursday Sensex expiry. GIFT Nifty only if labeled as not an NSE or BSE cash print. |
| `institutional-flows` | FII/FPI and DII cash, participant-wise F&O open interest, bulk and block deals. Every row carries a session date and `previous_session` freshness. |
| `market-breadth` | Advance/decline, new highs and lows, and whether a few index names are carrying the move. Score only fields the script returned. |
| `sector-rotation` | NSE and BSE sector indices versus Nifty or Sensex over 5, 20, and 60 sessions. |
| `options-positioning` | Nearest listed expiry, put-call ratio, change in open interest around spot, India VIX, days to expiry, freeze quantity and lot size from the contract file. No strategy recommendation in this skill. |
| `levels-plan` | Previous-day and weekly high and low, VWAP, central pivot range, opening range. Computed, then read. |
| `indian-desk` | Routes a request to one skill. It does not redo the analysis itself. |

### Phase 3 — Company events

**Not started.**

| Skill | Job |
| --- | --- |
| `fundamentals` | Quarterly and annual lines, ratios, pledge, shareholding. Indian fiscal year, April to March. |
| `concall-reader` | Guidance, capex, and what management declined to answer, from a transcript the research skill already located. |
| `corporate-actions` | Dividend, split, bonus, rights, buyback, OFS, board meeting, ex-date. From exchange announcements. |
| `results-calendar` | Upcoming board meetings and results for a watchlist, from announcements. |

### Phase 4 — A decision, still without sending an order

**Not started.** A plan requires a surveillance result and a tape or levels result already on disk.

| Skill | Job |
| --- | --- |
| `trade-plan` | Horizon in Indian product language (intraday cash, delivery, futures, options), entry, invalidation, target, R multiple. |
| `position-size` | Risk in rupees, round down to the board lot or the F&O lot, charges from `data/costs.json`. A quantity, not an order. |
| `risk-gate` | PASS or BLOCK against daily loss, trades already planned, reward to risk, results day, expiry day, ban, circuit, and stale data. BLOCK stops the chain. |
| `trade-journal` | Append-only local log with IST time, setup name, planned risk, and later outcome. |

### Phase 5 — After the desk has been used

**Not started.** These wait until the earlier phases are used on real questions.

| Skill | Job |
| --- | --- |
| `scanner` | Opening-range breaks and high-delivery names inside a named list. Banned and trade-for-trade names excluded by default. |
| `backtest-india` | Costs from the dated charge sheet, slippage in ticks, expiry week called out. A run that ignores STT fails. |
| `paper-ticket` | A manual ticket you can type into a broker. A human yes is stored in the journal. No broker API and no live order in this phase. |

NSE currency derivatives and NSE commodity derivatives stay out of all five phases unless the scope is explicitly widened. MCX and NCDEX stay out.

## Layout

```
.claude/skills/          Claude Code skills (SKILL.md plus references)
src/indian_market/       Resolver, clock, expiry, costs, surveillance, analysis, tape, brief checker
data/symbols.json        Starter book of NSE symbols and BSE scrip codes
data/holidays.json       2026 closures and the Muhurat session
data/costs.json          Dated charge sheet
data/fixtures/           Recorded samples the tests and --demo use
evals/phase1.md          Prompts for checking the skills in a fresh session
tests/                   Offline unittest suite. No network.
```

## Tests

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -v
```

The suite covers the universe refusal, the Diwali expiry shift, Muhurat hours, the SAIL ban demo, the opening-range boundary at 09:30, unsourced SWOT and research notes, and the presence of each Phase 1 skill.

## Scope

In: NSE equity cash, including SME series named as such. BSE equity cash, including BSE SME. NSE and BSE equity indices. Equity and index futures and options on those two exchanges.

Out: MCX, NCDEX, crypto, US and other foreign listings, 13F filings, and treating a GIFT Nifty print as an NSE cash price.

## License

[MIT](LICENSE)
