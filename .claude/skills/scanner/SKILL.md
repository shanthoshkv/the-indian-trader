---
name: scanner
description: >
  Finds opening-range breaks and high-delivery names inside a named NSE or
  BSE list. Use when the user asks to scan a list or for a scanner. Banned
  and trade-for-trade names are excluded unless the pack says otherwise.
  NSE and BSE only.
---

# Scanner

The scan stays inside the named list. It does not scan the market, and it does not recompute the opening range. The pack supplies `opening_range_high` and `opening_range_low` from tape-reading or levels-plan.

Not investment advice.

## Steps

1. Build the list the user named. Set `min_delivery_pct` from the user. Do not invent a threshold.
2. Carry ban and trade-for-trade flags from surveillance. They are excluded unless `include_restricted` is true.

```json
{
  "source": "fixture:scan",
  "session_date": "2026-11-06",
  "min_delivery_pct": 50,
  "names": [
    {"symbol": "RELIANCE", "exchange": "NSE", "last": 114, "opening_range_high": 113, "opening_range_low": 111, "delivery_pct": 62}
  ]
}
```

3. Run:

```
$env:PYTHONPATH = "src"
python -m indian_market.cli scan --fixture path\to\list.json
```

`--demo` is `data/fixtures/scan_list.json`. The demo threshold is 50 because that file sets it.

## Output

```
Scan · session date
Not investment advice.

| Symbol | Hit or exclusion | Value | Source |
| --- | --- | --- | --- |

Missing: one line for each item with ok false.
```

A name can have both an opening-range break and `high_delivery`. Quote both rows. `scan_excluded` is `fo_ban` or `trade_for_trade`. A symbol outside NSE and BSE is a missing `scan_hit`, not a hit. A name inside the range and under the delivery threshold produces no row. Do not add it.
