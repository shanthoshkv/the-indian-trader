# Changelog

All notable changes to this project are documented in this file.

The version line is the state of the skill pack. Phases that are not listed as shipped are specified in the README and are not implemented.

## [Unreleased]

## [0.4.0] - 2026-11-07

### Added

- The risk gate reads a `mandate` object when the pack or `gate --mandate` supplies one. A missing key is not checked. `data/mandate.json` is a blank template and is not loaded by itself. Null caps do not block
- `book` quotes gross, net, weight, days-to-exit, and open planned risk from open journal rows and a price file. It does not resize. The desk command for book risk is `book`. The other five book skills stay without a calculator
- `check-brief` accepts `thesis`, `short`, and `ic`. An IC decision line that is not empty fails. A bullet that starts with buy or sell fails
- `fetch` also parses delivery, bulk and block deals, ASM, GSM, ESM, MWPL, shareholding, pledge, and constituents. A blank pledge is not zero. A missing constituent weight stays blank. New kinds have no default URL
- `session-pack` reads a folder of those files. A missing file stays blank. It does not run the morning chain
- BSE equity cash transaction charge `bse_txn_equity` at 0.00375% each side for groups A, B, and other non-exclusive scrips, reviewed 2026-11-06. BSE futures and options stay blank. The charge is not inside the backtest net
- Stamp duty is an Article 56A rate from `stamp_rate` only after `buyer_state` is named. `stamp_duty` itself stays null. Stamp is not deducted from quantity and is not inside the backtest net
- Journal review adds `horizon_hit_rate`, `expiry_week_hit_rate`, and `net_after_charges_inr`. `net_after_stt_inr` is unchanged
- A backtest adjusts prices only when `actions` supplies `price_factor` and `ex_date` and the trade has `entry_time`. An incomplete list fails that trade. The demo without actions is unchanged
- The holiday list is stale after its review date plus 180 days. Dates through 2027-05-05 stay confirmed. A later date is not a confirmed session

## [0.3.0] - 2026-11-07

### Added

- Book skills with no calculator: `mandate`, `thesis-memo`, `short-case`, `book-risk`, `pair-note`, and `ic-note`. The desk routes them with command `none`

## [0.2.0] - 2026-11-07

### Added

- Phase 2 skills and commands: `premarket`, `flows`, `breadth`, `rotation`, `options`, `levels`, and `desk`
- Phase 3 skills and commands: `fundamentals`, `concall`, `actions`, and `results`
- Concall notes can be checked with `check-brief --kind concall`
- Sector indexes used by rotation: Nifty IT, Auto, FMCG, Metal, Pharma, and BSE Auto
- A stock symbol is no longer given Nifty's weekly expiry
- Phase 4 skills and commands: `plan`, `size`, `gate`, `journal-show`, `journal-add`, `journal-outcome`
- Phase 5 skills and commands: `scan`, `backtest`, `ticket`
- Append-only local journal. `data/journal.jsonl` is gitignored. `--demo` does not write it
- A backtest with `include_stt` not true exits 2 and publishes no net
- A paper ticket stores a human yes in the journal only when the risk gate is PASS. Nothing is sent to a broker
- Phase 6 setup cards: `setup --name` for opening range, previous day, VWAP hold, delivery and relative strength, sector leader, and post-result
- `morning` runs surveillance, a named-list scan, one setup, size, and the gate. BLOCK writes no ticket
- `journal-review` reports hit rate, average realized R, and net after STT. `journal-outcome` stores `--realized-r` and `--exit-price`. `--demo` does not write
- `fetch` parses a local official file or tries one `--url`. A failed download leaves the field blank and is cached only after a successful read, under `data/cache/`
- `series` reports verified, unverified, and refused names and does not rewrite `data/symbols.json`
- NSE transaction charges from NSE/FA/73061 (27 February 2026) and the SEBI turnover fee sit beside STT. They are not inside the backtest net. Stamp duty and the BSE transaction rate stay blank
- Futures and options plans stay incomplete without expiry and lot size. Options also need a strike and CE or PE
- The risk gate can block a Muhurat session, a tight rupee circuit, an ex-date, a record date, a board meeting, or open planned risk at the daily limit. Those checks run only when the pack supplies the key

### Still blank

- Stamp duty has no single rate on the sheet
- BSE has no transaction rate on the sheet
- A public download that fails is a blank field, not a guessed price

A command with no fixture still exits 2 and leaves the field blank. Asking the desk to place an order stays `no_route`. No command calls a broker.

## [0.1.0] - 2026-11-06

### Added

- Phase 0 core library `indian_market`: symbol resolver, IST session clock, 2026 holiday list, expiry calendar, dated charge sheet, evidence objects
- Phase 1 skills: `market-core`, `surveillance-check`, `market-research`, `market-analysis`, `swot-analysis`, `tape-reading`
- CLI: `resolve`, `session`, `expiry`, `costs`, `surveillance`, `analyze`, `tape`, `check-brief`
- Demo fixtures for a Reliance bar pack, a Reliance session tape, a SAIL F&O-ban clearance, and a sourced research note
- Offline unittest suite, including the refusal of US tickers and MCX
- `evals/phase1.md` prompts for checking the skills in a fresh Claude Code session

### Market rules frozen into this release

- Cash session 09:15–15:30 IST, with the 7 September 2026 pre-open split
- Nifty weekly expiry on Tuesday, Sensex weekly expiry on Thursday, holiday-shifted to the previous trading session
- No weekly contract for Bank Nifty, Fin Nifty, Midcap Select, or stock F&O
- Muhurat trading on 8 November 2026, 14:20–15:30 IST
- Holiday list from NSE circular NSE/CMTR/71775 (12 December 2025). 15 January 2026 kept as BSE-only
- Charge sheet reviewed 6 November 2026, stale after 180 days

### Notes

- `--demo` output is fixture data, not a live quote
- Analysis, tape, and surveillance commands exit 2 when no evidence file is passed
- Research and SWOT briefs fail `check-brief` when a bullet has no source, or when the note contains a buy or sell verdict
- No broker connection and no order placement
