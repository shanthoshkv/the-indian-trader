---
name: mandate
description: >
  Records the book rules the user supplies before any NSE or BSE idea is
  sized. Use when the user asks for a trading mandate or a book mandate.
  Does not invent limits. NSE and BSE only.
---

# Mandate

Write the book rules down before a name is discussed. Every limit comes from the user. A blank limit is not a default.

Not investment advice. This is not an order.

## Steps

1. Ask for the fields below that are missing. Do not fill them from another fund's reported limits.

```json
{
  "source": "fixture:mandate",
  "book_inr": null,
  "horizon": ["delivery"],
  "direction": "long_only",
  "single_name_cap_pct": null,
  "sector_cap_pct": null,
  "gross_band": null,
  "net_band": null,
  "daily_loss_limit_inr": null,
  "max_participation_pct": null,
  "allow_muhurat": false,
  "allow_sme": false,
  "allow_short": false
}
```

`horizon` may include `intraday_cash`, `delivery`, and `futures`. Options stay descriptive. `direction` is `long_only` or `long_short`. A short, when allowed, is a future or a cash sale that can be delivered. It is not a naked short.

2. Resolve any symbol the user names. Stop on `outside_universe`.

```
$env:PYTHONPATH = "src"
python -m indian_market.cli resolve SYMBOL
```

The desk label `mandate` is not a CLI subcommand. Do not run it.

3. Refuse a fresh derivative when surveillance says the name is in F&O ban. Refuse intraday cash when the series is trade-for-trade or BE. Refuse SME when `allow_sme` is false. Refuse a Muhurat session when `allow_muhurat` is false. These checks use surveillance-check and market-core. They do not replace risk-gate.

## Output

```
Mandate
Not investment advice.

| Rule | Value | Source |
| --- | --- | --- |

Missing: one line for each limit the user did not supply.
```

Nobody overrides a BLOCK from risk-gate. Quote the rules back. Do not size a name in this skill.
