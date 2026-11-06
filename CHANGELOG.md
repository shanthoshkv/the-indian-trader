# Changelog

All notable changes to this project are documented in this file.

The version line is the state of the skill pack. Phases that are not listed as shipped are specified in the README and are not implemented.

## [Unreleased]

### Planned

- Phase 2: `premarket-brief`, `institutional-flows`, `market-breadth`, `sector-rotation`, `options-positioning`, `levels-plan`, `indian-desk`
- Phase 3: `fundamentals`, `concall-reader`, `corporate-actions`, `results-calendar`
- Phase 4: `trade-plan`, `position-size`, `risk-gate`, `trade-journal`
- Phase 5: `scanner`, `backtest-india`, `paper-ticket`
- Live NSE and BSE file downloads, behind the same evidence JSON the skills already require

None of these skills exist in the tree yet. Asking for them should not produce a made-up flow or a made-up option chain.

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
