---
name: pair-note
description: >
  Writes a relative note for two NSE or BSE names, or one name against its
  sector index. Use when the user asks for a pair note or a pair trade.
  Does not estimate a hedge ratio. NSE and BSE only.
---

# Pair note

One relative claim. Both legs have to be inside NSE or BSE. This is not two separate tips.

Not investment advice. This is not an order.

## Steps

1. Resolve both symbols. If one is `outside_universe`, stop. Do not replace it.
2. Read sector-rotation for the sector indexes already in the file. If the two names are not in the same sector, say so and leave the pair incomplete.
3. The user writes the claim: why A against B, and over what window.

```json
{
  "source": "fixture:pair",
  "session_date": "2026-11-06",
  "long_symbol": "INFY",
  "short_symbol": "NIFTYIT",
  "claim": "",
  "window": "",
  "hedge_ratio": null,
  "invalidation": null
}
```

The desk label `pair-note` is not a CLI subcommand. Sector figures come from:

```
$env:PYTHONPATH = "src"
python -m indian_market.cli rotation --fixture path\to\rotation.json
```

4. Write these sections.

- **Claim.** The user's sentence. Do not improve it into a verdict.
- **Sector.** The rotation row, or "sectors differ."
- **Hedge ratio.** Quote `hedge_ratio` only when the user supplied it. Do not estimate a beta.
- **Breaks.** What would end the pair: both legs fall together, the sector de-rates, one name is in F&O ban, one name hits a circuit, one reports and the other does not. A ban or a circuit is quoted from surveillance-check, not from memory.
- **Invalidation.** The user's level for the spread. Missing invalidation means the pair is incomplete.
- **Expression.** Each short leg also has to pass short-case. No option structure on either leg.

## Output

```
Pair · A against B
complete | incomplete
Not investment advice.

| Section | Value | Source |
| --- | --- | --- |

Missing: one line for each input the user did not supply.
```
