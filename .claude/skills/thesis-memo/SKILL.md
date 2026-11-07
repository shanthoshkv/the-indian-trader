---
name: thesis-memo
description: >
  Organizes one NSE or BSE claim into a sourced memo: evidence, variant,
  catalyst, cases, and kill criteria. Use when the user asks for an
  investment thesis or a thesis memo. The claim is the user's. NSE and BSE only.
---

# Thesis memo

The user states the claim. This skill puts evidence next to it and leaves gaps blank. It does not upgrade the claim into a buy or a sell.

Not investment advice. This is not an order.

## Steps

1. Resolve the symbol. Stop on `outside_universe`. If the mandate skill has rules on disk, drop the idea when it breaks one. A dropped idea does not get the rest of this memo.
2. Take numbers only from commands already run, or from a file those commands checked. The desk label `thesis-memo` is not a CLI subcommand. After the memo is written, run `check-brief --kind thesis` on that file. A failed check is not a finished memo.

Read, when the user has the files:

- `fundamentals` and `concall-reader` for the business, margins, return on capital, and capital allocation
- `fundamentals` for promoter holding and pledge
- `market-research` for one named peer
- `sector-rotation` for the sector index against Nifty or Sensex
- `results-calendar` and `corporate-actions` for dates
- `tape`, `market-analysis`, and `institutional-flows` for what has already happened

3. Write the sections in this order. Skip none. A missing input is a blank row.

- **Claim.** One sentence: what changes, at which event, against which invalidation. No target price.
- **Micro.** Only lines those commands returned.
- **Governance.** Promoter holding, pledge, related-party transactions, auditor note, cash flow against profit, contingent liabilities. A blank pledge is not "no pledge."
- **Industry.** The sector row and the one named peer. Do not add a peer from memory.
- **Macro.** A rates, rupee, or policy line only when the user pasted a source. Crude, gold, and a US listing are not positions.
- **Variant.** One consensus sentence with a filing, a concall line, or a figure the user pasted. One sentence on what differs. No source means the variant is blank.
- **Drivers.** Say whether the claim is about earnings, the multiple, or both. If the user did not supply one of them, name the missing one. Do not multiply an earnings figure by a multiple.
- **Catalyst path.** Each date from the calendar or the corporate-action file gets "what we need to see" and "what would mean the claim failed."
- **Setup.** State the move so far from tape and relative strength on disk. State who is already in it from flows, delivery, and open interest on disk.
- **Cases.** Bull, base, and bear. A price, a probability, or a rupee payoff appears only when the user wrote it.
- **Kill criteria.** The facts that retire the idea: a missed line, a pledge increase, a ban, a circuit, a broken invalidation, a stale source.
- **Pre-mortem.** "The planned risk was lost." Mark each cause as a scenario unless a command already returned it: the claim was wrong, the timing was wrong, liquidity, governance, the whole sector, crowding, stale data.

## Output

```
Thesis · SYMBOL · Exchange · Series
Not investment advice.

| Section | What is on disk | Source |
| --- | --- | --- |

Missing: one line for each section that has no source.
```

Do not invent the R multiple. trade-plan and position-size own those figures.
