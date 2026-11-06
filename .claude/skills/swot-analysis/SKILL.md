---
name: swot-analysis
description: >
  Builds an auditable SWOT for one NSE or BSE listed company from cited
  filings. Use when the user asks for a SWOT, strengths and weaknesses,
  or the risks of an Indian listed company. NSE and BSE only.
---

# SWOT analysis

A SWOT that can be checked. Each line names the filing it came from.

Not investment advice.

## When to run

The user asks for a SWOT. Run market-research first when you do not already have cited filings. This skill does not invent a moat.

## What counts

- Strengths and weaknesses: reported margins, returns, debt, promoter holding, pledge, a related-party note, or an ASM or GSM flag that surveillance-check returned.
- Opportunities and threats: a line from a concall or presentation, a regulation, or a competitor that is itself listed on the NSE or BSE.
- A line with no source is left out. "Strong brand" and "experienced management" are left out unless a filing says so.

## Steps

1. Resolve the symbol with market-core. Stop on `outside_universe`.
2. Draft the note with the template. Every bullet has `source:` and `date:`.
3. Check it:

```
$env:PYTHONPATH = "src"
python -m indian_market.cli check-brief path\to\swot.md --kind swot
```

4. Exit 2 lists the missing headings and unsourced bullets. Fix them and run the check again.

## Output

```
SYMBOL · Exchange · Series · Session date
Surveillance: fact only, not a trade block
Not investment advice. Figures are from the sources named below.

## Strengths
- point | evidence: ... | source: https://... or NSE filing id | date: YYYY-MM-DD

## Weaknesses
- point | evidence: ... | source: ... | date: ...

## Opportunities
- point | evidence: ... | source: ... | date: ...

## Threats
- point | evidence: ... | source: ... | date: ...

## What would flip
- point | evidence: ... | source: ... | date: ...
```

A heading with nothing cited contains `None cited.` and no bullet.

## Hand off

Stop after the flip condition. Do not add a buy or sell rating.
