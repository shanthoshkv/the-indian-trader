---
name: backtest-india
description: >
  Replays NSE or BSE round trips with STT from the dated charge sheet,
  slippage in ticks, and an expiry-week flag. Use when the user asks for a
  backtest. A run that ignores STT fails. NSE and BSE only.
---

# Backtest

The command returns net, STT, slippage, and whether the exit sits in an expiry week. Quote those fields. A run that does not set `include_stt` to true fails. Do not publish a net for that run.

Not investment advice. This does not place an order.

## Steps

1. Put `tick_size` in the pack from the security file. This command does not fall back to the cash tick schedule. `slippage_ticks` is required. Zero is allowed only when the pack says 0.
2. Each trade needs entry, exit, qty, and `exit_time`. For a stock, pass `expiry_date` when the week should be called out. Index weeks use the next Nifty or Sensex expiry on or after the exit.

```json
{
  "symbol": "RELIANCE",
  "exchange": "NSE",
  "series": "EQ",
  "source": "fixture:backtest",
  "horizon": "intraday_cash",
  "include_stt": true,
  "slippage_ticks": 1,
  "tick_size": 1,
  "trades": [
    {"side": "long", "entry": 112, "exit": 118, "qty": 10, "exit_time": "2026-11-24T15:20:00+05:30", "expiry_date": "2026-11-24"}
  ]
}
```

The demo tick size is 1 so the sample arithmetic is exact. A live Reliance cash tick comes from the security file, not from this sample.

3. Run:

```
$env:PYTHONPATH = "src"
python -m indian_market.cli backtest --fixture path\to\backtest.json
```

`--demo` is `data/fixtures/backtest_reliance.json`.

## Output

```
Backtest · SYMBOL · Exchange · Series
Not investment advice.

| Field | Value | Session | Source |
| --- | --- | --- | --- |

Missing: one line for each item with ok false.
```

Slippage is inside the fill. STT uses `data/costs.json` on the adjusted prices. If `error` is `stt_required`, or a trade's STT row is not ok, stop. There is no net. That includes an exit date outside the charge sheet's review window. `net_pnl_inr` is the adjusted gross minus STT, and minus GST only when the trade supplied brokerage. `exchange_txn_inr` is a separate field and is not inside that net. A BSE fill, or a stale sheet, leaves the exchange transaction charge blank. Quote `max_drawdown_inr` and `horizon_net_pnl_inr` when those rows are ok. Expiry week is true when the exit and the expiry date share an ISO week.
