---
name: position-size
description: >
  Sizes one NSE or BSE plan from rupee risk, floored to the lot in the pack,
  and estimates STT from data/costs.json. Use when the user asks for a
  position size or how many shares. A quantity, not an order. NSE and BSE only.
---

# Position size

The command returns the quantity. Do not recompute it, and do not hardcode a lot.

Not investment advice. This is not an order.

## Steps

1. Start from a trade-plan whose `plan_status` is `ready`. Carry the horizon, entry, invalidation, and clearance.
2. Put `lot_size` in the pack from the contract file or the board lot. If it is missing, leave quantity blank.
3. Put `risk_inr` and `as_of` (the charge-sheet date). Add `brokerage_inr` only when the user supplied a brokerage figure.

```json
{
  "symbol": "RELIANCE",
  "exchange": "NSE",
  "series": "EQ",
  "session_date": "2026-11-06",
  "as_of": "2026-11-06",
  "source": "fixture:size",
  "plan_status": "ready",
  "horizon": "intraday_cash",
  "entry": 112,
  "invalidation": 109,
  "risk_inr": 1000,
  "lot_size": 1
}
```

4. Run:

```
$env:PYTHONPATH = "src"
python -m indian_market.cli size --fixture path\to\size.json
```

`--demo` is `data/fixtures/size_reliance.json`.

## Output

```
Size · SYMBOL · Exchange · Series
Not investment advice. Not an order.

| Field | Value | Session | Source |
| --- | --- | --- | --- |

Missing: one line for each item with ok false.
```

Quantity is price risk only, floored to `lot_size`. Charges are not deducted from it. STT, the exchange transaction charge, and the SEBI turnover fee come from `data/costs.json` as separate fields. NSE uses the NSE rows. BSE equity cash uses `bse_txn_equity`. BSE futures and options leave the exchange transaction charge blank. Stamp stays blank unless `buyer_state` is in the pack. GST appears only when brokerage was in the pack. The GST base is that brokerage plus the exchange transaction charge when that charge is present. GST is not applied to STT.

Fresh F&O on a blocked name, and intraday cash on a trade-for-trade or BE series, have no quantity. Hand a `ready` quantity to risk-gate. Do not turn it into an order.
