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

Quote `hit_rate`, `avg_r`, `net_after_stt_inr`, and `open_risk_inr`. Open rows are excluded from the hit rate and counted in open risk. Net is gross minus STT. The exchange transaction charge is not inside that net. A row the command marks missing stays blank.
