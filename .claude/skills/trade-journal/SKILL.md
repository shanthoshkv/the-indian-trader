---
name: trade-journal
description: >
  Reads and appends a local NSE or BSE trade journal: IST time, setup, planned
  risk, and a later outcome. Use when the user asks for the trade journal.
  The demo does not write. NSE and BSE only.
---

# Trade journal

The log is append-only. A new line is added. Earlier lines are not rewritten.

Not investment advice. A journal line is not an order.

## Steps

1. To read the sample, run:

```
$env:PYTHONPATH = "src"
python -m indian_market.cli journal-show --demo
```

`--demo` reads `data/fixtures/journal_sample.jsonl` and does not touch the live log.

2. To read or append the live log, pass `--path`. The default live path is `data/journal.jsonl`. That file is gitignored.

```
$env:PYTHONPATH = "src"
python -m indian_market.cli journal-show --path path\to\journal.jsonl
python -m indian_market.cli journal-add --fixture path\to\plan.json --path path\to\journal.jsonl
python -m indian_market.cli journal-outcome --path path\to\journal.jsonl --id PLAN-ID --outcome target_hit --realized-r 2 --exit-price 110
```

A plan line needs a symbol, a setup name, `planned_risk_inr`, and a source. An outcome is `target_hit`, `stopped`, `open`, or `scratched`. Buy and sell are not outcomes. An outcome for an id that is not already in the file writes nothing. `--demo` does not append. Hit rate and net after STT belong to journal-review.

## Output

```
Journal · path
Not investment advice.

| Id | Symbol | Setup | Planned risk (INR) | Outcome | Logged at IST |
| --- | --- | --- | --- | --- | --- |
```

Quote `entries`. An unknown id stays unknown. Do not invent a line the command did not write. `journal-add --demo` shows the sample and does not append.
