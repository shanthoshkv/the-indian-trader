---
name: concall-reader
description: >
  Pulls guidance, capex, and what management declined to answer from a
  transcript the research note already located. Use when the user asks
  about a concall, a transcript, guidance, or capex comments on an NSE or
  BSE company. NSE and BSE only.
---

# Concall reader

Use a transcript you can point at. A topic with no excerpt stays blank. Do not invent a decline, a guidance number, or a capex number.

Not investment advice.

## Steps

1. Resolve the symbol. Stop on `outside_universe`. Locate the transcript the same way market-research locates a filing. This skill starts once that transcript exists.
2. Copy excerpts into a pack. `topic` is `guidance`, `capex`, or `declined`. Each excerpt needs its own source, a URL, an NSE or BSE id, or `fixture:`.

```json
{
  "symbol": "RELIANCE",
  "exchange": "NSE",
  "series": "EQ",
  "session_date": "2025-10-17",
  "source": "fixture:reliance-q2fy26-concall",
  "fiscal_period": "Q2 FY2026",
  "excerpts": [
    {"topic": "guidance", "speaker": "CFO", "text": "Retail revenue growth for the year is guided in the mid teens.", "source": "fixture:concall#12:04"}
  ]
}
```

3. Run:

```
$env:PYTHONPATH = "src"
python -m indian_market.cli concall --fixture path\to\concall.json
```

`--demo` is `data/fixtures/concall_reliance.json`.

4. Write the note from the items. Quote the excerpt. Then check it:

```
python -m indian_market.cli check-brief path\to\note.md --kind concall
```

Required headings are Guidance, Capex, and Declined. A heading with no excerpt says `None cited.` and has no bullet. Every bullet has `source:`. The note fails if it contains a buy or sell verdict.

## Output

```
Concall · SYMBOL · fiscal period · session date
Not investment advice.

## Guidance

## Capex

## Declined
```

One bullet per ok item: `text | evidence | source: ... | date: ...`. Skip items with ok false, and name the missing topic.
