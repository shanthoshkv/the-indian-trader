# Changelog

All notable changes to this project are documented in this file.

The version line is the state of the skill pack. Phases that are not listed as shipped are specified in the README and are not implemented.

## [Unreleased]

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
- Book skills with no calculator: `mandate`, `thesis-memo`, `short-case`, `book-risk`, `pair-note`, and `ic-note`. The desk routes them with command `none`

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
