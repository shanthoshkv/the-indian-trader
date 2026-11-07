---
name: indian-desk
description: >
  Routes one NSE or BSE question to the skill that owns it. Use when the
  user asks the desk to handle a market question, or when the job is not
  named. Does not calculate the figure itself. NSE and BSE only.
---

# Indian desk

This skill picks a skill. It does not answer the market question.

Not investment advice. No order is placed.

## Steps

1. Run:

```
$env:PYTHONPATH = "src"
python -m indian_market.cli desk "the user question"
```

2. When `ok` is true, open the named skill and follow it. Use its command. Do not compute the figure in this skill. A setup card, the morning chain, a journal review, and an official file are separate skills.
3. When `error` is `ambiguous`, ask which of `candidates` the user wants. Do not pick one.
4. When `error` is `no_route`, say this pack does not have that job. Do not draft an order. A journal line, a scan row, or a ticket exists only when that skill's command wrote it.
5. A symbol `resolve` marks `outside_universe` stops here. Say NSE and BSE only.

The router is a hint. If the user already named a skill, use that skill.
