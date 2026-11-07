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
2. Quote the open book from `book`. It reads open journal rows and a price file. Closed rows stay out. It does not cut a position.

```
$env:PYTHONPATH = "src"
python -m indian_market.cli book --fixture path\to\book.json
```

`--demo` is `data/fixtures/book.json`. Hit rate stays with journal-review. Quote `open_risk_inr` from this command next to the mandate loss limit. Do not recompute either figure.

3. Fill these rows from the command. A missing price, volume, book size, or cap stays blank.

- **Gross and net.** Quote `gross_inr` and `net_inr`.
- **Weights.** Quote `weight_pct` and `sector_weight_pct`. A missing weight is not zero. Report `cap_breach` and do not cut it.
- **Open risk.** The open planned risk against the daily loss limit.
- **Overlap.** Two open ideas that share a sector, a promoter group, or a results week, and only when those links are in the files.
- **Liquidity.** Quote `days_to_exit`. Do not divide a position by a volume that was not in the file.
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
