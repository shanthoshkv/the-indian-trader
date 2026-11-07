---
name: options-positioning
description: >
  Reads the nearest listed expiry, put-call ratio, open-interest change near
  spot, India VIX, days to expiry, lot size, and freeze quantity from a
  contract file. Use when the user asks about the option chain, PCR, or
  positioning on an NSE or BSE index or stock. No strategy recommendation.
  NSE and BSE only.
---

# Options positioning

The chain comes from the file. Lot size and freeze quantity are copied from that file. This skill does not recommend a strategy.

Not investment advice.

## Steps

1. Resolve the symbol. Stop on `outside_universe`. Bank Nifty, Fin Nifty, Midcap Select, and single stocks have no weekly in `market-core`. Use the expiry printed in the contract file, not a remembered weekday.
2. Build the pack. Omit `lot_size` and `freeze_qty` when the contract file does not contain them.

```json
{
  "symbol": "NIFTY",
  "exchange": "NSE",
  "series": "INDEX",
  "session_date": "2026-11-05",
  "source": "fixture:nse-fo-bhavcopy",
  "spot": 25500,
  "expiry": "2026-11-09",
  "lot_size": 65,
  "freeze_qty": 1800,
  "india_vix_close": 12.4,
  "india_vix_session": "2026-11-05",
  "strikes": [{"strike": 25500, "call_oi": 200, "put_oi": 300, "call_oi_change": 15, "put_oi_change": -5}]
}
```

3. Run:

```
$env:PYTHONPATH = "src"
python -m indian_market.cli options --fixture path\to\chain.json
```

`--demo` is `data/fixtures/options_nifty.json`. Label the lot and the chain as a fixture.

## What the command scores

- `put_call_ratio` is total put open interest divided by total call open interest on the strikes supplied.
- Open-interest change around spot uses strikes within 1 percent of spot. If none sit in that band, it uses the nearest strike.
- India VIX is the previous close named by `india_vix_session`.
- An expiry before the session date is left blank.

## Output

```
Options · SYMBOL · Exchange · session date
Not investment advice. No strategy is recommended.

| Field | Value | Session | Freshness | Source |
| --- | --- | --- | --- | --- |

Missing: one line for each item with ok false.
```

Do not add a preferred strike, a credit spread, or a buy or sell.
