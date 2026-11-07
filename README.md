# The Indian Trader

Claude Code skills for people who trade **only on the NSE and the BSE**.

The pack is a research desk, not a broker and not a tip service. Every price, delivery figure, and open-interest label has to come from a command in this repo, with a source and a session date. If the command has no figure, the note leaves the field blank. Nothing here places an order.

This is not a SEBI-registered research analyst, and it is not investment advice.

## What you can ask today

Phases 0 through 6 are shipped. Open this repo in Claude Code and the skills in `.claude/skills/` load on their own. You pass a JSON file, or you use `--demo`. `fetch --url` can try one public NSE file. A failed download leaves the field blank. Nothing here places an order.

| Skill | Ask it |
| --- | --- |
| `market-core` | Is the market open? When is Nifty expiry? What is the STT snapshot? Which exchange is this symbol? |
| `surveillance-check` | Is this name in F&O ban, ASM, GSM, ESM, or trade-for-trade? |
| `market-research` | What does this listed company do, and what did the filings just say? |
| `market-analysis` | Where is price, delivery, relative strength versus Nifty or Sensex, and futures buildup? |
| `swot-analysis` | SWOT, where every bullet needs a filing or an exchange source |
| `tape-reading` | Opening range, VWAP, previous-day high and low, on bars you actually have |
| `premarket-brief` | Previous close, FII and DII for the last completed session, India VIX, this week's expiries. Pre-open only after 09:00 IST. |
| `institutional-flows` | FII and DII cash, participant open interest, bulk and block deals, with the session date on every row |
| `market-breadth` | Advances, declines, new highs and lows, and whether a few names carry the index |
| `sector-rotation` | Sector index versus Nifty or Sensex over 5, 20, and 60 sessions |
| `options-positioning` | Nearest listed expiry, put-call ratio, open interest near spot, lot size and freeze quantity from the file |
| `levels-plan` | Previous-day and weekly range, VWAP, central pivot, opening range |
| `indian-desk` | Routes the question to one skill. It does not redo the calculation. |
| `fundamentals` | Quarterly and annual lines, pledge, and shareholding. Fiscal year is April to March. |
| `concall-reader` | Guidance, capex, and what management declined to answer, from a transcript you supply |
| `corporate-actions` | Dividend, split, bonus, rights, buyback, OFS, board meeting, ex-date |
| `results-calendar` | Upcoming board meetings and results for a watchlist |
| `trade-plan` | Horizon, entry, invalidation, target, and R, from a surveillance result and a tape or levels result already on disk |
| `position-size` | Quantity from rupee risk, floored to the lot in the file. Charges come from `data/costs.json`. Not an order |
| `risk-gate` | PASS or BLOCK. BLOCK stops the chain |
| `trade-journal` | Append-only local log. The demo does not write |
| `scanner` | Opening-range breaks and high delivery inside a named list. Ban and trade-for-trade are excluded by default |
| `backtest-india` | Round trips with the dated charge sheet, slippage in ticks, and expiry week. A run that ignores STT fails |
| `paper-ticket` | Text a person can type into a broker. A human yes is stored in the journal. No broker API |
| `opening-range-break` | Setup card from the last price and the opening range already on disk |
| `previous-day-break` | Setup card from the previous-day high and low |
| `vwap-hold` | Long card when price is above VWAP and the opening-range low holds |
| `delivery-rs` | Delivery card when delivery and relative strength clear thresholds you supplied |
| `sector-leader` | That delivery card only when the name's sector is the leader already named |
| `post-result` | Next-session gap card. The results session itself stays blocked |
| `morning-chain` | Premarket, surveillance, scan, one setup, size, and the gate. BLOCK writes no ticket |
| `journal-review` | Hit rate, average R, and net after STT. Open rows stay out of the hit rate |
| `official-files` | Parse a bhavcopy, ban file, or contract file. A series report does not rewrite the starter book |
| `mandate` | Book rules the user supplies. No invented limit |
| `thesis-memo` | One claim, with the variant, the catalyst, and the kill criteria left blank where the file is blank |
| `short-case` | The other side of a claim, and whether a short can be expressed |
| `book-risk` | The open book against the mandate. Does not resize |
| `pair-note` | One name against another, or against its sector index. No estimated hedge |
| `ic-note` | One page assembled from the skills above. The decision stays blank |

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
python -m indian_market.cli premarket --demo
python -m indian_market.cli flows --demo
python -m indian_market.cli breadth --demo
python -m indian_market.cli rotation --demo
python -m indian_market.cli options --demo
python -m indian_market.cli levels --demo
python -m indian_market.cli fundamentals --demo
python -m indian_market.cli concall --demo
python -m indian_market.cli actions --demo
python -m indian_market.cli results --demo
python -m indian_market.cli plan --demo
python -m indian_market.cli size --demo
python -m indian_market.cli gate --demo
python -m indian_market.cli journal-show --demo
python -m indian_market.cli scan --demo
python -m indian_market.cli backtest --demo
python -m indian_market.cli ticket --demo
python -m indian_market.cli setup --name orb --demo
python -m indian_market.cli morning --demo
python -m indian_market.cli journal-review --demo
python -m indian_market.cli fetch --kind cash_bhav --demo
python -m indian_market.cli series --demo
python -m indian_market.cli desk "put call ratio on nifty"
```

`--demo` replays recorded samples in `data/fixtures/`. Those rows are marked `fixture`. They are not a live quote. `journal-show --demo`, `journal-add --demo`, `journal-outcome --demo`, and `journal-review --demo` read a sample and do not append. A live journal is `data/journal.jsonl`, which is gitignored.

`analyze`, `tape`, `surveillance`, and the later evidence commands refuse to run with no file. Pass `--fixture path\to\pack.json`, or `--demo`. `fetch` takes `--file`, `--demo`, or `--url`. The JSON shapes are in each skill's `SKILL.md`. `desk` only names the skill. It does not compute the figure. `journal-outcome` appends to a path you pass, and it can store `--realized-r` and `--exit-price`. `ticket --path` stores a human yes only when the gate is PASS and the plan id is already in that journal. No command calls a broker.

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

**Shipped.** One skill per job. The router does not reimplement the others. Each command still needs a fixture or `--demo`. Nothing here downloads nseindia.com or bseindia.com.

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

**Shipped.** Filings and announcements you already have. A missing excerpt, pledge, or meeting stays blank.

| Skill | Job |
| --- | --- |
| `fundamentals` | Quarterly and annual lines, ratios, pledge, shareholding. Indian fiscal year, April to March. |
| `concall-reader` | Guidance, capex, and what management declined to answer, from a transcript the research skill already located. |
| `corporate-actions` | Dividend, split, bonus, rights, buyback, OFS, board meeting, ex-date. From exchange announcements. |
| `results-calendar` | Upcoming board meetings and results for a watchlist, from announcements. |

### Phase 4 — A decision, still without sending an order

**Shipped.** A plan requires a surveillance result and a tape or levels result already on disk. The gate can BLOCK. BLOCK is a finished answer and stops the chain. The journal appends a line. It does not rewrite earlier lines, and it does not send anything.

| Skill | Job |
| --- | --- |
| `trade-plan` | Horizon in Indian product language (intraday cash, delivery, futures, options), entry, invalidation, target, R multiple. |
| `position-size` | Risk in rupees, round down to the board lot or the F&O lot, charges from `data/costs.json`. A quantity, not an order. |
| `risk-gate` | PASS or BLOCK against daily loss, trades already planned, reward to risk, results day, expiry day, ban, circuit, and stale data. BLOCK stops the chain. |
| `trade-journal` | Append-only local log with IST time, setup name, planned risk, and later outcome. |

### Phase 5 — After the desk has been used

**Shipped.** The scanner stays inside the named list. The backtest fails when STT is left out. The paper ticket is text for a person to type. A human yes is stored in the journal only after the gate is PASS. No broker API.

| Skill | Job |
| --- | --- |
| `scanner` | Opening-range breaks and high-delivery names inside a named list. Banned and trade-for-trade names excluded by default. |
| `backtest-india` | Costs from the dated charge sheet, slippage in ticks, expiry week called out. A run that ignores STT fails. |
| `paper-ticket` | A manual ticket you can type into a broker. A human yes is stored in the journal. No broker API and no live order in this phase. |

### Phase 6 — Setup cards, the morning chain, and official files

**Shipped.** Each setup card calls the trade plan. A failed trigger is `invalid` or `blocked`, and it is not sized. The morning chain stops before a ticket when the gate is BLOCK. The journal review reports hit rate, average realized R, and net after STT. Open rows stay out of the hit rate.

`fetch` parses a cash bhavcopy, an F&O bhavcopy, a ban file, a contract file, an FII file, or an announcement file you already have. `--url` tries one public file and caches it under `data/cache/`, which is gitignored. Any download error leaves the field blank. The tests do not call the exchange. `series` counts verified, unverified, and refused names and does not rewrite `data/symbols.json`.

The NSE equity, futures, and options transaction charges, and the SEBI turnover fee, are on the charge sheet from 1 March 2026 and are quoted beside STT. They are not inside the backtest net. From 0.4.0, BSE equity cash for groups A, B, and other non-exclusive scrips uses `bse_txn_equity`. BSE futures and options stay blank. Stamp duty is quoted only when the pack names `buyer_state`. GST applies to brokerage plus the exchange transaction charge when brokerage was supplied, and not to STT. Futures and options plans stay incomplete without an expiry and a lot size. An option also needs a strike and CE or PE.

| Skill | Job |
| --- | --- |
| `opening-range-break` | Last price through the opening range. A BE series blocks intraday cash. |
| `previous-day-break` | Last price through the previous-day high or low. |
| `vwap-hold` | Long only, above VWAP, with the opening-range low held. |
| `delivery-rs` | Delivery horizon. Both thresholds have to be in the pack. |
| `sector-leader` | The same delivery test, and only when the name's sector is the named leader. |
| `post-result` | The next trading session after results. The results day itself is blocked. |
| `morning-chain` | One pack from surveillance through the gate. No ticket after BLOCK. |
| `journal-review` | Hit rate, average R, net after STT, open planned risk. |
| `official-files` | Parse an exchange file, or report series coverage. No invented BSE code. |

### The book

**Shipped.** Five of these skills still have no calculator and do not end in a buy or a sell. `book-risk` quotes the `book` command. That command multiplies an open quantity by a price that is already in the file. It does not resize, and it does not draft an order. A missing price, volume, or cap stays blank. The risk gate reads a mandate only when the pack or `--mandate` points at one. `data/mandate.json` is a blank template and is not loaded by itself.

| Skill | Job |
| --- | --- |
| `mandate` | Horizon, direction, caps, and what the book refuses. |
| `thesis-memo` | Evidence, variant, catalyst path, three cases, kill criteria, pre-mortem. |
| `short-case` | How the claim fails, and whether that side is expressible. |
| `book-risk` | Concentration, open planned risk, overlap, liquidity, one named stress. |
| `pair-note` | A relative claim inside NSE and BSE. |
| `ic-note` | The page a person reads. The decision line stays empty. |

NSE currency derivatives and NSE commodity derivatives stay out unless the scope is explicitly widened. MCX and NCDEX stay out.

## Layout

```
.claude/skills/          Claude Code skills (SKILL.md plus references)
src/indian_market/       Resolver, clock, expiry, costs, and the evidence commands
data/symbols.json        Starter book of NSE symbols and BSE scrip codes
data/holidays.json       2026 closures and the Muhurat session
data/costs.json          Dated charge sheet
data/mandate.json        Blank mandate template. The gate does not load it unless asked
data/fixtures/           Recorded samples the tests and --demo use
evals/                   Prompts for checking the skills in a fresh session
tests/                   Offline unittest suite. No network.
```

## Tests

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -v
```

The suite covers the universe refusal, the Diwali expiry shift, Muhurat hours, the SAIL ban demo, the opening-range boundary at 09:30, unsourced SWOT and research notes, the Phase 2 session commands, the Phase 3 filing commands, the Phase 4 plan, size, gate, and journal, the Phase 5 scan, backtest, and paper ticket, the Phase 6 setup cards, morning chain, journal review, and official-file parser, the 0.4.0 book, mandate, session folder, and charge-sheet checks, and the presence of each skill. The official-file test uses a fixture or a URL that fails before any network call.

## Scope

In: NSE equity cash, including SME series named as such. BSE equity cash, including BSE SME. NSE and BSE equity indices. Equity and index futures and options on those two exchanges.

Out: MCX, NCDEX, crypto, US and other foreign listings, 13F filings, and treating a GIFT Nifty print as an NSE cash price.

## License

[MIT](LICENSE)
