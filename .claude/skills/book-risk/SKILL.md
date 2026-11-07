---
name: book-risk
description: >
  Reads the open NSE or BSE book against the user's mandate: concentration,
  open planned risk, overlap, and liquidity. Use when the user asks for book
  risk or portfolio risk. Does not resize a position. NSE and BSE only.
---

# Book risk

This skill reads the journal and the mandate. It does not change a size and it does not replace risk-gate.

Not investment advice. This is not an order.

## Steps

1. Read the mandate. Limits the user did not write stay blank.
2. Read the open book from the journal. The demo journal is not the live book.

```
$env:PYTHONPATH = "src"
python -m indian_market.cli journal-review --path path\to\journal.jsonl
```

`--demo` reviews the sample file and writes nothing. Quote `open_risk_inr`. Put it next to `daily_loss_limit_inr` from the mandate. Do not recompute either figure.

The desk label `book-risk` is not a CLI subcommand.

3. Fill these rows only from values the user or a command already supplied. Do not multiply quantity by price in this skill.

- **Gross and net.** Quote `gross_inr` and `net_inr` when the user wrote them. Otherwise blank.
- **Weights.** Quote each name's weight and each sector's weight when the user wrote them, and compare with the mandate caps. A missing weight is not zero.
- **Open risk.** The journal figure against the daily loss limit.
- **Overlap.** Two open ideas that share a sector, a promoter group, or a results week, and only when those links are in the files.
- **Liquidity.** Quote days-to-exit when the user wrote it. Do not divide a position by volume here.
- **Stress.** One case the user names. Fill it only when a beta or a circuit distance is already in a command result. Otherwise the row is blank.
- **Cut.** The mandate rule that would force a reduction. Do not import another fund's drawdown ladder.

## Output

```
Book
Not investment advice.

| Row | Value | Mandate | Source |
| --- | --- | --- | --- |

Missing: one line for each row that was not supplied.
```

A name that would break a cap is reported. This skill does not cut it and does not draft an order.
