---
name: ic-note
description: >
  Assembles one NSE or BSE idea into a one-page note from the mandate, the
  thesis, the short case, the book, the size, and the gate. Use when the
  user asks for an investment committee note or an IC note. Does not pick
  the outcome. NSE and BSE only.
---

# IC note

Assemble what the other skills already wrote. Leave the decision blank.

Not investment advice. This is not SEBI-registered research. This is not an order.

## Steps

1. Read, and do not redo:

- mandate
- thesis-memo
- short-case
- book-risk, or write "book not supplied"
- position-size, only if a plan is `ready`
- risk-gate

2. The desk label `ic-note` is not a CLI subcommand. Size and the gate, when they exist, come from their own commands. Copy `quantity` and `gate`. Do not recompute them.

3. Write one page, in this order.

- **Mandate.** Inside the rules, or the rule it breaks.
- **Thesis.** Five lines: claim, variant, catalyst date, kill criterion, and the blank that still matters. If the variant or the date is blank, say blank.
- **Other side.** Three lines from the short case, including `expressible` or `not expressible`.
- **Book.** The name's weight and the open-risk line, or "book not supplied."
- **Size and gate.** The copied quantity and PASS or BLOCK. A missing plan has no quantity.
- **Decision.** Leave this empty for the user: pass, research more, or accept a plan that already passed the gate. Do not tick a box. Do not draft an order.

## Output

```
IC note · SYMBOL · Exchange · Series
Not investment advice. Not an order.

| Block | On disk | Source |
| --- | --- | --- |

Decision:

Missing: one line for each block that was not run.
```

BLOCK stops the page at the gate. Do not continue into a ticket.
