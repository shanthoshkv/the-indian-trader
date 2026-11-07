---
name: paper-ticket
description: >
  Writes a manual NSE or BSE ticket a person can type into a broker, and
  stores a human yes in the local journal. Use when the user asks for a
  paper ticket or a manual ticket. No broker API and no live order.
  NSE and BSE only.
---

# Paper ticket

The command prints text. A person types it. Nothing in this skill contacts a broker.

Not investment advice.

## Steps

1. Require a risk-gate result of PASS. Any other gate produces no ticket.
2. Match the product to the horizon: `intraday_cash` is MIS, `delivery` is CNC, `futures` and `options` are NRML. Side is `buy` or `sell`. Quantity is the sized quantity.
3. A LIMIT ticket needs `limit_price`. `human_yes` is JSON true or the string `yes`.

```json
{
  "symbol": "RELIANCE",
  "exchange": "NSE",
  "series": "EQ",
  "session_date": "2026-11-06",
  "source": "fixture:ticket",
  "id": "RELIANCE-2026-11-06T09:20:00+05:30",
  "horizon": "intraday_cash",
  "product": "MIS",
  "side": "buy",
  "quantity": 333,
  "gate": "PASS",
  "order_type": "LIMIT",
  "limit_price": 112,
  "validity": "DAY",
  "human_yes": false
}
```

4. Run:

```
$env:PYTHONPATH = "src"
python -m indian_market.cli ticket --fixture path\to\ticket.json --path path\to\journal.jsonl
```

`--demo` is `data/fixtures/ticket_reliance.json`. Demo does not write, even if `--path` is passed.

The journal must already contain that plan id. Without a human yes, or without a journal path, the status stays `draft` and the yes is not stored. With both, status is `ready` and one `human_yes` line is appended.

## Output

```
Ticket · SYMBOL · Exchange · Series
Status: draft | ready | blocked | invalid
Not investment advice. Nothing was sent to a broker.

<the ticket text, two lines>
```

Quote the `ticket` value. On the demo, status is `draft` because `human_yes` is false. Do not mark it sent. Do not add a broker route.
