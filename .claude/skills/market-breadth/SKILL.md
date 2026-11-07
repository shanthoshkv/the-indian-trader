---
name: market-breadth
description: >
  Scores NSE or BSE advance and decline, new highs and lows, and whether a
  few index names carry the move. Use when the user asks about breadth,
  advances, declines, new highs, or market internals. NSE and BSE only.
---

# Market breadth

Score only the fields the command returned. A missing high-low count stays blank.

Not investment advice.

## Steps

1. Build a pack from the exchange breadth file and, when you have them, index point contributions.

```json
{
  "session_date": "2026-11-05",
  "exchange": "NSE",
  "source": "fixture:nse-breadth",
  "advances": 1200,
  "declines": 800,
  "unchanged": 50,
  "new_highs": 40,
  "new_lows": 15,
  "contributors": [{"symbol": "RELIANCE", "points": 50}]
}
```

Leave out `new_highs` or `contributors` when the file has neither. Do not estimate them from an index move.

2. Run:

```
$env:PYTHONPATH = "src"
python -m indian_market.cli breadth --fixture path\to\breadth.json
```

`--demo` is `data/fixtures/breadth.json`. The demo has no new-high count. Say that it is missing.

## How to read concentration

Quote the label. `narrow` means one name is at least 40 percent of the absolute index-point contribution among the names supplied. `broad` means no name reached that share. `flat` means the contributions summed to zero. Fewer than three names leaves the label blank.

## Output

```
Breadth · Exchange · session date
Not investment advice.

| Field | Value | Freshness | Source |
| --- | --- | --- | --- |

Missing: one line for each item with ok false.
```
