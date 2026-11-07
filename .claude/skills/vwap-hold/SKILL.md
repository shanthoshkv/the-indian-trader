---
name: vwap-hold
description: >
  Builds a VWAP-hold setup card for one NSE or BSE symbol when price is
  above VWAP and the opening-range low is held. Use when the user asks for
  a VWAP hold. A plain VWAP read stays with tape-reading. NSE and BSE only.
---

# VWAP hold

The card is long only. It does not invent a short.

Not investment advice. This is not an order.

## Steps

1. Carry last, `vwap`, and `opening_range_low` from tape-reading. Carry a surveillance result.

```json
{
  "symbol": "RELIANCE",
  "exchange": "NSE",
  "series": "EQ",
  "session_date": "2026-11-06",
  "source": "fixture:vwap",
  "last": 114,
  "vwap": 112,
  "opening_range_low": 111,
  "surveillance": {"clearance": "clear", "source": "fixture:surveillance", "session_date": "2026-11-06"}
}
```

2. Run:

```
$env:PYTHONPATH = "src"
python -m indian_market.cli setup --name vwap --fixture path\to\setup.json
```

`--demo` is `data/fixtures/setup_vwap.json`.

## Output

```
Setup · vwap_hold · SYMBOL
Status: ready | blocked | invalid | incomplete
Not investment advice.

| Field | Value | Session | Source |
| --- | --- | --- | --- |

Missing: one line for each item with ok false.
```

Invalidation is VWAP. If last is not above VWAP, or last is under the opening-range low, the card is `invalid`.
