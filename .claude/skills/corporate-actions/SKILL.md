---
name: corporate-actions
description: >
  Lists dividend, split, bonus, rights, buyback, OFS, board meeting, and
  ex-date rows from exchange announcements for one NSE or BSE symbol. Use
  when the user asks about a corporate action or an ex-date. NSE and BSE only.
---

# Corporate actions

Rows come from the announcement file. A kind the file does not support, or a row without a source, stays blank.

Not investment advice.

## Steps

1. Resolve the symbol. Stop on `outside_universe`.
2. Build the pack. `kind` is `dividend`, `split`, `bonus`, `rights`, `buyback`, `ofs`, or `board_meeting`.

```json
{
  "symbol": "RELIANCE",
  "exchange": "NSE",
  "source": "fixture:nse-announcements",
  "actions": [
    {
      "kind": "dividend",
      "headline": "Interim dividend Rs 5 per share",
      "ex_date": "2026-11-14",
      "session_date": "2026-11-02",
      "source": "NSE/RELIANCE/2026/dividend"
    }
  ]
}
```

Omit `ex_date` when the announcement has none. Do not guess it from a board-meeting date.

3. Run:

```
$env:PYTHONPATH = "src"
python -m indian_market.cli actions --fixture path\to\actions.json
```

`--demo` is `data/fixtures/actions_reliance.json`.

## Output

```
Corporate actions · SYMBOL · Exchange
Not investment advice.

| Kind | Ex-date | Headline | Announcement date | Source |
| --- | --- | --- | --- | --- |

Missing: one line for each item with ok false.
```

A watchlist of upcoming meetings belongs to results-calendar. Do not rebuild that list here.
