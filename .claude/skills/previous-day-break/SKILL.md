---
name: previous-day-break
description: >
  Builds a previous-day high or low break setup card for one NSE or BSE
  symbol. Use when the user asks for a previous day break. NSE and BSE only.
---

# Previous day break

The card uses the previous-day high and low already on disk. It does not recompute them.

Not investment advice. This is not an order.

## Steps

1. Carry last, `prev_high`, and `prev_low`. Carry a surveillance result.

```json
{
  "symbol": "RELIANCE",
  "exchange": "NSE",
  "series": "EQ",
  "session_date": "2026-11-06",
  "source": "fixture:pdh",
  "last": 116,
  "prev_high": 114,
  "prev_low": 109,
  "surveillance": {"clearance": "clear", "source": "fixture:surveillance", "session_date": "2026-11-06"}
}
```

2. Run:

```
$env:PYTHONPATH = "src"
python -m indian_market.cli setup --name pdh --fixture path\to\setup.json
```

`--demo` is `data/fixtures/setup_pdh.json`.

## Output

```
Setup · previous_day_break · SYMBOL
Status: ready | blocked | invalid | incomplete
Not investment advice.

| Field | Value | Session | Source |
| --- | --- | --- | --- |

Missing: one line for each item with ok false.
```

A long break uses the previous-day high as invalidation. A short break uses the previous-day low. A last price inside the prior day is `invalid`.
