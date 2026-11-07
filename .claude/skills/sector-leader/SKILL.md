---
name: sector-leader
description: >
  Builds a delivery setup card for one NSE or BSE name only when its sector
  is the leading sector already named in the pack. Use when the user asks
  for a sector leader setup. It does not scan the market. NSE and BSE only.
---

# Sector leader

The leading sector comes from sector-rotation output already on disk. This card checks one name against that label.

Not investment advice. This is not an order.

## Steps

1. Put `leader` and `sector` in the pack. They must be the same index symbol. Then put the same delivery and relative-strength fields delivery-rs uses, including both thresholds.

```json
{
  "symbol": "INFY",
  "exchange": "NSE",
  "series": "EQ",
  "session_date": "2026-11-06",
  "source": "fixture:sector",
  "sector": "NIFTYIT",
  "leader": "NIFTYIT",
  "last": 1500,
  "prev_low": 1460,
  "delivery_pct": 60,
  "min_delivery_pct": 50,
  "rs": 4,
  "min_rs": 0,
  "surveillance": {"clearance": "clear", "source": "fixture:surveillance", "session_date": "2026-11-06"}
}
```

2. Run:

```
$env:PYTHONPATH = "src"
python -m indian_market.cli setup --name sector --fixture path\to\setup.json
```

`--demo` is `data/fixtures/setup_sector.json`.

## Output

```
Setup · sector_leader · SYMBOL
Status: ready | blocked | invalid | incomplete
Not investment advice.

| Field | Value | Session | Source |
| --- | --- | --- | --- |

Missing: one line for each item with ok false.
```

A name whose sector is not the leader is `invalid`. Do not widen the check into a market scan.
