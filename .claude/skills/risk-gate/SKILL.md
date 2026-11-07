---
name: risk-gate
description: >
  Returns PASS or BLOCK for one NSE or BSE plan against daily loss, planned
  trades, reward to risk, results day, expiry day, ban, circuit, and stale
  data. Use when the user asks for a risk gate. BLOCK stops the chain.
  NSE and BSE only.
---

# Risk gate

PASS and BLOCK are both finished answers. The command exits 0 either way. BLOCK stops the chain. Do not continue to a paper ticket.

Not investment advice.

## Steps

1. Use the R multiple from trade-plan and the surveillance clearance already on disk. Do not recompute R.
2. Fill every check. A missing check is a reason to block, not a reason to skip it.

```json
{
  "symbol": "RELIANCE",
  "exchange": "NSE",
  "series": "EQ",
  "session_date": "2026-11-06",
  "source": "fixture:gate",
  "horizon": "intraday_cash",
  "clearance": "clear",
  "fo_ban": false,
  "trade_for_trade": false,
  "near_circuit": false,
  "results_day": false,
  "expiry_day": false,
  "r_multiple": 2,
  "min_r": 1.5,
  "daily_loss_inr": 0,
  "daily_loss_limit_inr": 5000,
  "planned_trades": 0,
  "max_planned_trades": 3,
  "data_as_of_ist": "2026-11-06T09:20:00+05:30",
  "now_ist": "2026-11-06T09:25:00+05:30",
  "max_age_minutes": 30,
  "costs_as_of": "2026-11-06"
}
```

3. Run:

```
$env:PYTHONPATH = "src"
python -m indian_market.cli gate --fixture path\to\gate.json
```

`--demo` is `data/fixtures/gate_pass.json`.

## Output

```
Gate · SYMBOL · Exchange · Series
PASS | BLOCK
Not investment advice.

| Field | Value | Session | Source |
| --- | --- | --- | --- |

Reasons: the reasons list. On PASS, say every supplied check passed.
```

Collect every reason, not only the first. F&O ban blocks futures and options. Trade-for-trade blocks intraday cash. An expiry day blocks futures and options. A results day, a near-circuit flag, a daily loss at the limit, a full plan cap, stale evidence, or a stale charge sheet blocks every horizon. Cash on an expiry day is not blocked for that reason alone.

Four checks run only when the pack includes the key. Leave them out when you do not have them. Muhurat blocks when `muhurat` is true. A rupee circuit distance blocks when both `circuit_distance_inr` and `min_circuit_distance_inr` are present and the distance is inside the minimum. An ex-date, a record date, or a board meeting blocks when `ex_date_today`, `record_date_today`, or `board_meeting_today` is true. Open planned risk blocks when both `open_risk_inr` and `daily_loss_limit_inr` are present and open risk has reached the limit. The demo leaves these keys out and stays PASS.

On BLOCK, stop. Do not draft a ticket.

If the pack includes a `mandate` object, a broken rule in that object is a BLOCK. A missing mandate key is not checked. Do not load `data/mandate.json` unless the pack or `--mandate` points at it. Null caps do not block. This command does not size.
