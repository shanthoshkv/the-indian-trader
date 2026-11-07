---
name: premarket-brief
description: >
  Builds the NSE and BSE morning brief from the previous close, FII and DII
  cash, India VIX, overnight announcements, and this week's Nifty and Sensex
  expiries. Includes a pre-open print only after 09:00 IST. Use when the user
  asks for a premarket brief, the morning setup, or GIFT Nifty before the
  open. NSE and BSE only.
---

# Premarket brief

Previous session first. The pre-open print is added only once 09:00 IST has passed and the print itself is timestamped at or after 09:00.

Not investment advice.

## Steps

1. Run `python -m indian_market.cli session` when the user needs the clock. This skill does not restate the session timetable.
2. Build a pack from files you actually have. Leave a key out when the file has no such row. Shape:

```json
{
  "session_date": "2026-11-06",
  "as_of_ist": "2026-11-06T08:40:00+05:30",
  "source": "fixture:premarket",
  "closes": [{"symbol": "NIFTY", "exchange": "NSE", "value": 25500, "session_date": "2026-11-05"}],
  "flows_session_date": "2026-11-05",
  "fii_cash_crore": -1200.5,
  "dii_cash_crore": 900.2,
  "india_vix": {"close": 12.4, "session_date": "2026-11-05"},
  "announcements": [{"symbol": "RELIANCE", "exchange": "NSE", "headline": "Board meeting intimation", "source": "NSE/RELIANCE/2026/1", "session_date": "2026-11-05"}],
  "gift_nifty": {"value": 25610, "as_of_ist": "2026-11-06T08:30:00+05:30", "source": "https://vendor.example/gift"}
}
```

Add `preopen` only when you have an exchange or broker print. Do not label that print as NSE or BSE when the number is a GIFT Nifty quote. GIFT stays under `gift_nifty`, with its own source, and never with `"exchange": "NSE"`.

3. Run:

```
$env:PYTHONPATH = "src"
python -m indian_market.cli premarket --fixture path\to\premarket.json
```

`--demo` is the sample in `data/fixtures/premarket.json`. Say so.

## Output

```
Premarket · session date · as of IST
Not investment advice. Figures are from the sources named below.

| Field | Symbol | Value | Session | Freshness | Source |
| --- | --- | --- | --- | --- | --- |

Missing: one line for each item with ok false.
```

Quote `weekly_expiry` as the command printed it. FII, DII, and India VIX rows are the previous session named on the item. A GIFT row is not an NSE or BSE cash price. Say that in the same sentence as the number.

Hand off a single name to market-research, surveillance-check, or tape-reading. Do not redo those jobs here.
