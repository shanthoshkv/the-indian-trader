---
name: short-case
description: >
  Writes the other side of one NSE or BSE claim and checks whether a short
  can be expressed. Use when the user asks for a short case or a short
  thesis. Does not recommend a short or an option structure. NSE and BSE only.
---

# Short case

State how the long claim fails, or how a short would fail. Then say whether the mandate can express that side. Stop when it cannot.

Not investment advice. This is not an order.

## Steps

1. Resolve both the name and, if the user named one, the hedge. Stop on `outside_universe`.
2. Read surveillance-check. A fresh future on an F&O ban is not expressible. Cash is still cash. Do not decide the ban from memory.
3. Read the mandate. If `allow_short` is false, the output is "not in the mandate."

The desk label `short-case` is not a CLI subcommand. After the note is written, run `check-brief --kind short` on that file. A failed check is not a finished note.

4. Write these sections.

- **Failure.** The long claim, restated as the way it fails. Use only evidence already on disk.
- **Expression.** A cash short has to be deliverable. Naked short selling is outside this pack. Do not assume a securities-lending size or a borrow fee. If those figures are not in a file, leave them blank. Institutional day-trading of a short is outside this pack. A future is allowed only when the mandate includes `futures` and surveillance does not block it. No option structure.
- **Squeeze.** Rows you may quote when a command returned them: delivery, promoter holding, pledge, a results date, an ex-date, open interest. A missing row stays missing.
- **Asymmetry.** Say that a short's loss is not capped by the same distance as a long's. Do not invent a stop.
- **Result.** `expressible` or `not expressible`. A missing borrow, a ban, or a mandate that refuses shorts is `not expressible`. Do not offer a workaround.

## Output

```
Short case · SYMBOL · Exchange · Series
expressible | not expressible
Not investment advice.

| Section | What is on disk | Source |
| --- | --- | --- |

Missing: one line for each figure the file did not contain.
```
