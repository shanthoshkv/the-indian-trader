---
name: results-calendar
description: >
  Lists upcoming board meetings and results for a watchlist from exchange
  announcements. Use when the user asks when a company reports, or for the
  results calendar of named NSE or BSE symbols. NSE and BSE only.
---

# Results calendar

A meeting is listed when its date is on or after `as_of` and the symbol is on the watchlist. A name with no such row stays blank. Past meetings are not shown.

Not investment advice.

## Steps

1. Resolve every watchlist symbol. Drop a name `resolve` marks `outside_universe` and say so.
2. Build the pack from announcement rows you have.

```json
{
  "as_of": "2026-11-06",
  "source": "fixture:nse-announcements",
  "watchlist": ["RELIANCE", "TCS"],
  "meetings": [
    {
      "symbol": "RELIANCE",
      "exchange": "NSE",
      "purpose": "financial results",
      "meeting_date": "2026-11-14",
      "session_date": "2026-11-02",
      "source": "NSE/RELIANCE/2026/board"
    }
  ]
}
```

3. Run:

```
$env:PYTHONPATH = "src"
python -m indian_market.cli results --fixture path\to\results.json
```

`--demo` is `data/fixtures/results_calendar.json`. Reliance has a meeting. TCS does not, and the old Reliance date is before `as_of`.

## Output

```
Results calendar · as of date
Not investment advice.

| Symbol | Meeting date | Purpose | Announcement date | Source |
| --- | --- | --- | --- | --- |

Missing: one line for each watchlist symbol with no upcoming row.
```

The purpose text is the announcement's purpose. Do not upgrade a board meeting into "results" unless the row says so.
