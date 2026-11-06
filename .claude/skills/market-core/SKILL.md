---
name: market-core
description: >
  Answers the NSE and BSE session clock, holiday and Muhurat sessions,
  Nifty and Sensex expiry, tick-size rule, and the evidence format.
  Use when the user asks about Indian market timings, pre-open, Muhurat,
  expiry day, lot size, tick size, STT, or which exchange a symbol is on.
  NSE and BSE only.
---

# Market core

Shared clock, universe, and evidence rules for this pack. Other skills load this file instead of restating the rules.

Not investment advice.

## When to run

The user asks about timings, holidays, expiry, charges, or a symbol's exchange. Also run `resolve` before any other skill names a symbol.

## Steps

From the repo root:

```
$env:PYTHONPATH = "src"
python -m indian_market.cli resolve RELIANCE
python -m indian_market.cli session
python -m indian_market.cli expiry NIFTY
python -m indian_market.cli costs
```

Add `--exchange BSE` when the user names BSE. Add `--at 2026-11-06T10:00:00` to pin the clock. Naive datetimes are IST.

## How to read the result

- `ok: false` and `outside_universe`: say the name is not in this NSE and BSE pack, and stop.
- `verified: false`: the symbol was accepted as a candidate NSE name. Say it is not in the starter book and must be confirmed on the exchange quote page before a trade.
- `costs` with `ok: false`: the charge sheet is past its review date. Show the rates only with that warning.
- Copy expiry dates and session phase from the JSON. Do not recall a different expiry weekday.

## References

- Universe and symbol rule: [references/universe.md](references/universe.md)
- Session clock: [references/sessions.md](references/sessions.md)
- Expiry: [references/expiry.md](references/expiry.md)
- Charges: [references/costs.md](references/costs.md)
- Evidence object: [references/evidence.md](references/evidence.md)
