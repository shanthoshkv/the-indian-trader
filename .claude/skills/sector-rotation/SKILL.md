---
name: sector-rotation
description: >
  Compares NSE and BSE sector indexes with Nifty or Sensex over 5, 20, and
  60 sessions. Use when the user asks which sector is leading or lagging the
  benchmark, or for sector rotation. NSE and BSE only.
---

# Sector rotation

Relative strength is the sector return minus the Nifty or Sensex return on the same dates. A window without enough dates stays blank.

Not investment advice.

## Steps

1. The benchmark is `NIFTY` or `SENSEX`. Sector symbols must resolve. `NIFTYIT`, `NIFTYAUTO`, `NIFTYFMCG`, `NIFTYMETAL`, `NIFTYPHARMA`, and `BSEAUTO` are indexes in this pack. Whether a stock is in an index comes from `fetch --kind constituents`. A missing weight stays blank. This skill does not keep a list of members.
2. Build the pack from daily closes you have. Do not invent the missing days.

```json
{
  "session_date": "2026-11-05",
  "source": "fixture:nse-sector-indices",
  "benchmark": {"symbol": "NIFTY", "exchange": "NSE", "bars": [{"date": "2026-11-05", "close": 1030}]},
  "sectors": [{"symbol": "NIFTYIT", "exchange": "NSE", "bars": [{"date": "2026-11-05", "close": 1100}]}]
}
```

3. Run:

```
$env:PYTHONPATH = "src"
python -m indian_market.cli rotation --fixture path\to\rotation.json
```

`--demo` is `data/fixtures/rotation.json`. It has six sessions, so the 20-session and 60-session rows are missing. Say so.

## Output

```
Sector rotation versus NIFTY or SENSEX · session date
Not investment advice.

| Sector | Window | Relative strength percent | Source |
| --- | --- | --- | --- |

Missing: one line for each item with ok false.
```

A positive `rs_5d_pct` means the sector beat the benchmark over those five sessions. Quote the field name and the detail, which names the benchmark.
