---
name: tape-reading
description: >
  Reads the Indian session tape: opening range, VWAP, previous day high
  and low, delivery, and futures open interest. Use when the user asks to
  read the tape, ticks, VWAP, opening range, or intraday flow on NSE or BSE.
  Names the data mode. NSE and BSE only.
---

# Tape reading

The first line of the note names the mode. Session mode is minute bars and the previous bhavcopy. Print mode is a time-and-sales feed. Yahoo minute bars are not exchange ticks.

Not investment advice.

## When to run

The user asks for the tape, ticks, VWAP, the opening range, or where price is versus the previous day's high and low. For the multi-day setup, use market-analysis.

## Steps

1. Resolve the symbol with market-core. Stop on `outside_universe`.
2. Run surveillance-check before any trade language. Quote its clearance.
3. Build a pack. Session mode:

```json
{
  "symbol": "RELIANCE",
  "exchange": "NSE",
  "series": "EQ",
  "mode": "session",
  "source": "broker-1m-bars",
  "freshness": "live_snapshot",
  "session_date": "2026-11-06",
  "prev_high": 110.0,
  "prev_low": 104.0,
  "prev_close": 108.0,
  "delivery_pct": 50.0,
  "delivery_session": "2026-11-05",
  "bars_1m": [{"t": "09:15", "h": 108.4, "l": 107.6, "c": 108.0, "v": 100}]
}
```

Leave out fields you do not have. Print mode sets `"mode": "prints"` and supplies `prints: [{"t": "09:16:01", "price": 108.1, "qty": 500, "side": "at_ask"}]`. Without that array, print mode returns a blank.

4. Run:

```
$env:PYTHONPATH = "src"
python -m indian_market.cli tape --fixture path\to\tape.json
```

`--demo` is a fixture. Say so.

## How the numbers are defined

- Opening range is 09:15 inclusive to 09:30 exclusive IST. The 09:30 bar is the first bar after the range.
- VWAP is the typical price `(high + low + close) / 3`, weighted by the volume on the bars supplied. The note says that, because a true exchange VWAP uses traded prices.
- Delivery percent during the session is the previous session's bhavcopy. The item's freshness will say `previous_session`.

## Output

```
Mode: session | prints · SYMBOL · Exchange · Series
Surveillance: clear | caution | blocked | not run
Not investment advice. Figures are from the sources named below.

| Field | Value | Session | Freshness | Source |
| --- | --- | --- | --- | --- |

Missing: list every item with ok false, in one line each.
```

Do not describe a missing VWAP as if you computed it.
