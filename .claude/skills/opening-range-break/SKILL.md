---
name: opening-range-break
description: >
  Builds an opening-range break setup card for one NSE or BSE symbol from
  the last price and the opening range already on disk. Use when the user
  asks for an opening range strategy or an ORB setup. NSE and BSE only.
---

# Opening range break

This is a setup card. It calls trade-plan. It does not scan a list. A scan for opening-range breaks stays with the scanner.

Not investment advice. This is not an order.

## Steps

1. Carry last, `opening_range_high`, and `opening_range_low` from tape-reading or levels-plan. Carry a surveillance result.
2. A BE series is trade-for-trade. The card then blocks intraday cash.

```json
{
  "symbol": "RELIANCE",
  "exchange": "NSE",
  "series": "EQ",
  "session_date": "2026-11-06",
  "source": "fixture:orb",
  "last": 114,
  "opening_range_high": 113,
  "opening_range_low": 111,
  "surveillance": {"clearance": "clear", "source": "fixture:surveillance", "session_date": "2026-11-06"}
}
```

3. Run:

```
$env:PYTHONPATH = "src"
python -m indian_market.cli setup --name orb --fixture path\to\setup.json
```

`--demo` is `data/fixtures/setup_orb.json`.

## Output

```
Setup · opening_range_break · SYMBOL
Status: ready | blocked | invalid | incomplete
Not investment advice.

| Field | Value | Session | Source |
| --- | --- | --- | --- |

Missing: one line for each item with ok false.
```

Quote entry, invalidation, target, and R from the command. A last price inside the range is `invalid`. Do not size a card that is not `ready`.
