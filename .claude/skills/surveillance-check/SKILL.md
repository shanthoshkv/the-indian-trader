---
name: surveillance-check
description: >
  Checks an NSE or BSE symbol for series, price band, ASM, GSM, ESM,
  trade-for-trade, and F&O ban. Use before a trade idea or a tape read,
  and when the user asks if a stock is in ban, in ASM, or trade-for-trade.
  NSE and BSE only.
---

# Surveillance check

Clearance for one symbol. Cash research of a banned name can continue. Fresh F&O on a banned name stops.

Not investment advice.

## Steps

1. Resolve the symbol with market-core. Stop on `outside_universe`.
2. Build a facts JSON from an exchange file you actually downloaded (ban list, security file). Required keys: `symbol`, `exchange`, `series`, `fo_ban`, `trade_for_trade`, `asm_stage`, `gsm_stage`, `esm`, `price_band_pct`, `near_circuit`, `lot_size`, `session_date`, `source`, `freshness`. Use null when the file has no such field. Do not guess a stage.
3. Run:

```
$env:PYTHONPATH = "src"
python -m indian_market.cli surveillance --fixture path\to\facts.json --segment cash
```

Use `--segment fo` when the user is asking about futures or options. `--demo` runs the SAIL ban sample and must be labeled as a fixture.

## How to read clearance

| clearance | Meaning |
| --- | --- |
| clear | No flag in the facts file |
| caution | Name the flags. Cash discussion can continue |
| blocked | Fresh F&O is stopped. Say that cash may still trade |

Quote `session_date`, `source`, and `freshness`. If the user has no facts file, say the check was not run. Do not declare the name clean from memory.
