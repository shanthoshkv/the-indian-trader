---
name: levels-plan
description: >
  Computes the previous-day high and low, the weekly high and low, VWAP,
  the central pivot range, and the opening range for one NSE or BSE symbol.
  Use when the user asks for levels, the pivot, CPR, or the day's range.
  NSE and BSE only.
---

# Levels

The command computes the levels. The note reads them. Do not replace a computed level with one from memory.

Not investment advice.

## Steps

1. Resolve the symbol. Stop on `outside_universe`. Run surveillance-check before any trade language.
2. Build a pack of daily bars. Add minute bars when you have them. A bar dated on `session_date` is not the previous day.

```json
{
  "symbol": "RELIANCE",
  "exchange": "NSE",
  "series": "EQ",
  "session_date": "2026-11-06",
  "source": "fixture:nse-cm-bhavcopy",
  "daily_bars": [{"date": "2026-11-05", "high": 114, "low": 109, "close": 112}],
  "bars_1m": [{"t": "09:15", "h": 112.4, "l": 111.6, "c": 112.0, "v": 100}]
}
```

3. Run:

```
$env:PYTHONPATH = "src"
python -m indian_market.cli levels --fixture path\to\levels.json
```

`--demo` is `data/fixtures/levels_reliance.json`.

## What the fields are

The previous high, low, and close are the last daily bar before `session_date`. The weekly high and low use completed bars in that ISO week only. VWAP and the opening range use the same definitions as tape-reading: typical price weighted by volume, and 09:15 inclusive to 09:30 exclusive. `cpr_pivot`, `cpr_top`, and `cpr_bottom` come from that previous bar.

## Output

```
Levels · SYMBOL · Exchange · Series
Surveillance: clear | caution | blocked | not run
Not investment advice.

| Field | Value | Session | Source |
| --- | --- | --- | --- |

Missing: one line for each item with ok false.
```

Hand off the session tape to tape-reading when the user wants prints or a running VWAP story. Do not recompute the pivot in prose.
