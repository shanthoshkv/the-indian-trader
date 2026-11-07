---
name: trade-plan
description: >
  Turns a surveillance result and a tape or levels result already on disk
  into an NSE or BSE plan: horizon, side, entry, invalidation, target, and
  R multiple. Use when the user asks for a trade plan or to plan the trade.
  NSE and BSE only.
---

# Trade plan

The command scores the plan. Quote its fields. Do not size a plan whose `plan_status` is not `ready`.

Not investment advice. This is not an order.

## Steps

1. Resolve the symbol. Stop on `outside_universe`.
2. Put a surveillance result and a tape or levels result in the pack. Both have to already be on disk. The context needs one ok price field: previous high or low or close, VWAP, opening range, CPR, weekly high or low, or close.

```json
{
  "symbol": "RELIANCE",
  "exchange": "NSE",
  "series": "EQ",
  "session_date": "2026-11-06",
  "source": "fixture:plan",
  "horizon": "intraday_cash",
  "side": "long",
  "entry": 112,
  "invalidation": 109,
  "target": 118,
  "surveillance": {"clearance": "clear", "source": "fixture:surveillance", "session_date": "2026-11-06"},
  "levels": {"items": [{"ok": true, "field": "prev_high", "value": 114}]}
}
```

Horizon is `intraday_cash`, `delivery`, `futures`, or `options`. Side is `long` or `short`.

3. Run:

```
$env:PYTHONPATH = "src"
python -m indian_market.cli plan --fixture path\to\plan.json
```

`--demo` is `data/fixtures/plan_reliance.json`.

## Output

```
Plan · SYMBOL · Exchange · Series
Status: ready | blocked | invalid | incomplete
Not investment advice.

| Field | Value | Session | Source |
| --- | --- | --- | --- |

Missing: one line for each item with ok false.
```

`ready` can go to position-size. `blocked` means fresh F&O on a blocked clearance, or intraday cash on a trade-for-trade series. `invalid` means the invalidation or the target is on the wrong side of entry. `incomplete` means surveillance or the tape or levels context is missing. Futures and options also stay `incomplete` without `expiry_date` and `lot_size` from the contract file. An option also needs `strike` and `option_type` of CE or PE. Do not invent the R multiple.
