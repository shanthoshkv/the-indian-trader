---
name: market-analysis
description: >
  Reads price, delivery, relative strength, and futures open interest for
  one NSE or BSE symbol from an evidence file. Use when the user asks how
  a stock or index is set up, about delivery, buildup, or relative strength
  versus Nifty or Sensex. NSE and BSE only.
---

# Market analysis

What the market is doing to one name, from bars you can point at.

Not investment advice.

## When to run

The user asks for the setup, delivery, relative strength, or futures buildup. For the business, use market-research. For the opening range and VWAP, use tape-reading.

## Steps

1. Resolve the symbol with market-core. Stop on `outside_universe`.
2. Run surveillance-check when the user is framing a trade. Include its clearance in the header. A missing facts file is reported as "surveillance not run", not as clear.
3. Prepare a JSON pack:

```json
{
  "symbol": "RELIANCE",
  "exchange": "NSE",
  "series": "EQ",
  "source": "nse-cm-bhavcopy",
  "freshness": "previous_session",
  "as_of_ist": "2026-11-05T18:10:00+05:30",
  "bars": [{"date": "2026-11-05", "close": 108.0, "volume": 1500, "delivery_qty": 750}],
  "benchmark": {"symbol": "NIFTY", "bars": [{"date": "2026-11-05", "close": 1000}]},
  "futures": {"close": 108.5, "prev_close": 105.2, "oi": 1200, "prev_oi": 1000}
}
```

`source` names the file the bars came from. Omit `delivery_qty` or `futures` when you do not have them. Do not estimate either.

4. Run:

```
$env:PYTHONPATH = "src"
python -m indian_market.cli analyze --fixture path\to\pack.json
```

`--demo` is the Reliance sample in `data/fixtures/reliance_bars.json`. Label it as a fixture.

5. Write the note from the items. Skip any item with `ok: false`, and say which field was missing.

## Output

```
SYMBOL · Exchange · Series · Session date · source
Surveillance: clear | caution | blocked | not run
Not investment advice. Figures are from the sources named below.

Regime: one sentence that uses only ok items.

| Field | Value | Session | Freshness | Source |
| --- | --- | --- | --- | --- |
| close | | | | |

What would invalidate this read: one sentence tied to a level that is in the table.
```

`fut_oi_quadrant` labels are `long_buildup`, `short_buildup`, `long_unwinding`, `short_covering`, or `flat`. Quote the label. Do not rename it.

## Hand off

tape-reading for the session. market-research if the user asks why it moved and no filing is in hand yet.
