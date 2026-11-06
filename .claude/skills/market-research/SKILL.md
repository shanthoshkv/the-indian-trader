---
name: market-research
description: >
  Writes a sourced brief on one NSE or BSE company or index from filings
  and announcements. Use when the user asks what a listed Indian company
  does, what changed this quarter, who owns it, about a pledge, a concall,
  or listed peers. NSE and BSE only.
---

# Market research

What the business is, and what just changed, from documents. This skill does not say buy or sell.

Not investment advice.

## When to run

The user wants a company brief, a quarterly change, shareholding, a pledge, a concall, or peers. If they want the price setup, use market-analysis. If they want SWOT, use swot-analysis after this brief exists.

## Steps

1. Resolve the symbol with market-core. Stop on `outside_universe`.
2. Collect documents you can point at: NSE or BSE announcements, an annual report, a shareholding pattern, an investor presentation. Save the extracts you will cite. Each citation is an `https` URL or an NSE or BSE filing identifier.
3. Write the note with the template below. Every bullet contains `source:` and `date:`.
4. Check it:

```
$env:PYTHONPATH = "src"
python -m indian_market.cli check-brief path\to\brief.md --kind research
```

5. If the command exits 2, fix the problems it lists and run it again. Hand the user the note only after `ok` is true.

There is no live filing downloader in this version. If you have no document, say so and stop. Do not fill the brief from memory. `data/fixtures/reliance_research_ok.md` is a shape example, and its numbers are fixtures.

## Output

```
SYMBOL · Exchange · Series · Session date · Data mode
Surveillance: not a trade check
Not investment advice. Figures are from the sources named below.

## Business
- point | evidence: ... | source: https://... | date: YYYY-MM-DD

## Last quarter
- point | evidence: ... | source: ... | date: ...

## Shareholding
- point | evidence: ... | source: ... | date: ...

## Announcements
- point | evidence: ... | source: ... | date: ...

## Peers
- point | evidence: ... | source: ... | date: ...

## Open questions
- point | evidence: ... | source: ... | date: ...
```

Peers are other NSE or BSE listings. A section with nothing to cite has no bullets, and a single line `None cited.`

## Hand off

Offer market-analysis for the price and delivery picture, or swot-analysis if the user wants a SWOT built only from this note.
