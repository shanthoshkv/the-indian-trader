---
name: institutional-flows
description: >
  Reads FII and DII cash, participant-wise F&O open interest, and bulk or
  block deals for one completed session. Use when the user asks about FII,
  DII, FPI, participant open interest, or a bulk or block deal on NSE or BSE.
  NSE and BSE only.
---

# Institutional flows

Every cash, open-interest, and deal row belongs to the session date on the file. During the day that date is the previous session.

Not investment advice.

## Steps

1. Refuse a symbol that `resolve` marks `outside_universe` before you put it in a deal row.
2. Build the pack from the exchange file. Omit a leg the file does not have.

```json
{
  "session_date": "2026-11-05",
  "source": "NSE/FII-DII/2026-11-05",
  "cash": {"fii_cash_crore": -100, "dii_cash_crore": 80},
  "participant_oi": [{"participant": "FII", "future_long": 100, "future_short": 140}],
  "deals": [{"kind": "bulk", "symbol": "RELIANCE", "exchange": "NSE", "qty": 100000, "price": 1500, "client": "Example fund"}]
}
```

`participant` is FII, FPI, DII, Pro, or Client. `kind` is `bulk` or `block`.

3. Run:

```
$env:PYTHONPATH = "src"
python -m indian_market.cli flows --fixture path\to\flows.json
```

`--demo` is `data/fixtures/flows.json`. Label it as a fixture.

## Output

```
Flows · session date
Not investment advice. Figures are the previous session named below.

| Field | Symbol | Value | Unit | Freshness | Source |
| --- | --- | --- | --- | --- | --- |

Missing: one line for each item with ok false.
```

Do not call a number from today's session final. The freshness on a usable row is `previous_session` unless the source is a fixture.
