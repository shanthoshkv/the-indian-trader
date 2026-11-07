---
name: delivery-rs
description: >
  Builds a delivery setup card for one NSE or BSE symbol when delivery
  percent and relative strength both clear thresholds the user supplied.
  Use when the user asks for delivery and relative strength as a setup.
  NSE and BSE only.
---

# Delivery and relative strength

The horizon is delivery. Do not invent a delivery threshold or a relative-strength threshold.

Not investment advice. This is not an order.

## Steps

1. Carry `delivery_pct`, `rs`, `min_delivery_pct`, `min_rs`, last, and `prev_low`. Both minimums have to be in the pack.

```json
{
  "symbol": "RELIANCE",
  "exchange": "NSE",
  "series": "EQ",
  "session_date": "2026-11-06",
  "source": "fixture:delivery",
  "last": 112,
  "prev_low": 109,
  "delivery_pct": 62,
  "min_delivery_pct": 50,
  "rs": 5,
  "min_rs": 0,
  "surveillance": {"clearance": "clear", "source": "fixture:surveillance", "session_date": "2026-11-06"}
}
```

2. Run:

```
$env:PYTHONPATH = "src"
python -m indian_market.cli setup --name delivery --fixture path\to\setup.json
```

`--demo` is `data/fixtures/setup_delivery.json`. The demo minimum of 50 is in that file. It is not a default.

## Output

```
Setup · delivery_rs · SYMBOL
Status: ready | blocked | invalid | incomplete
Not investment advice.

| Field | Value | Session | Source |
| --- | --- | --- | --- |

Missing: one line for each item with ok false.
```

A missing threshold, or a figure below the threshold in the pack, is `invalid`. Invalidation is the previous low.
