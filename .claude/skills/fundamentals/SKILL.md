---
name: fundamentals
description: >
  Reads quarterly and annual lines, ratios, promoter pledge, and
  shareholding for one NSE or BSE company. Uses the Indian fiscal year,
  April to March. Use when the user asks for results numbers, pledge,
  holding, ROE, or the price to earnings from a filing. NSE and BSE only.
---

# Fundamentals

Lines come from the filing in the pack. A period label that disagrees with `period_end` is dropped. The fiscal year is April to March, and the annual row ends on 31 March.

Not investment advice.

## Steps

1. Resolve the symbol. Stop on `outside_universe`.
2. Build the pack from the result filing and the shareholding filing. Omit a line the filing does not print.

```json
{
  "symbol": "RELIANCE",
  "exchange": "NSE",
  "series": "EQ",
  "source": "fixture:reliance-results",
  "quarters": [{"period": "Q2 FY2026", "period_end": "2025-09-30", "sales": 1000, "pat": 100, "eps": 10}],
  "annual": [{"fiscal_year": "FY2025", "period_end": "2025-03-31", "sales": 4000, "pat": 400, "equity": 2000}],
  "price": {"value": 250, "session_date": "2026-11-05", "source": "fixture:nse-cm-bhavcopy"},
  "pledge": {"pct": 1.2, "as_of": "2025-09-30"},
  "shareholding": [{"holder": "promoter", "pct": 50.3, "as_of": "2025-09-30"}]
}
```

Q1 is April–June, Q2 July–September, Q3 October–December, Q4 January–March. Do not relabel a row to force a match.

3. Run:

```
$env:PYTHONPATH = "src"
python -m indian_market.cli fundamentals --fixture path\to\fundamentals.json
```

`--demo` is `data/fixtures/fundamentals_reliance.json`.

## Output

```
Fundamentals · SYMBOL · Exchange
Not investment advice. Figures are from the filings named below.

| Field | Value | Period end | Detail | Source |
| --- | --- | --- | --- | --- |

Missing: one line for each item with ok false.
```

`pe` is price divided by the latest quarterly earnings per share in the pack. It is not a trailing-twelve-month figure unless the filing said so and that line is in the table. `shareholding_sum_pct` adds the rows supplied. A partial table will not equal 100. Say that when it does not.

For the narrative around these numbers, hand off to market-research. Do not add a buy or sell.
