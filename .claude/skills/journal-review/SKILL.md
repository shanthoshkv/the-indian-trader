---
name: journal-review
description: >
  Reviews a local NSE or BSE journal for hit rate, average realized R, and
  net after STT by setup. Use when the user asks for a journal review. Open
  rows stay out of the hit rate. The demo does not write. NSE and BSE only.
---

# Journal review

This skill reads the log. It does not append. Writing a plan or an outcome stays with trade-journal.

Not investment advice. A review line is not an order.

## Steps

1. Pass the journal path. The sample review file is not the live log.

```
$env:PYTHONPATH = "src"
python -m indian_market.cli journal-review --demo
python -m indian_market.cli journal-review --path path\to\journal.jsonl
```

`--demo` reads `data/fixtures/journal_review.jsonl` and writes nothing.

2. An outcome that should count needs `target_hit`, `stopped`, or `scratched`, plus `realized_r`, `exit_price`, entry, quantity, side, and horizon on the plan line. trade-journal stores those with `journal-outcome --realized-r` and `--exit-price`.

## Output

```
Journal review · path
Not investment advice.

| Field | Value | Detail | Source |
| --- | --- | --- | --- |

Missing: one line for each item with ok false.
```

Quote `hit_rate`, `avg_r`, `net_after_stt_inr`, `net_after_charges_inr`, `horizon_hit_rate`, `expiry_week_hit_rate`, and `open_risk_inr`. Open rows are excluded from the hit rate and counted in open risk. `net_after_stt_inr` is gross minus STT. `net_after_charges_inr` also subtracts the exchange transaction charge, and GST or stamp only when that row supplied brokerage or a buyer state. If any closed row has no exchange rate, the full-cost field stays blank and the STT net remains. A row the command marks missing stays blank.
