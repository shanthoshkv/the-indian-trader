---
name: morning-chain
description: >
  Runs one NSE or BSE morning chain from a pack already on disk: optional
  premarket, surveillance, a named-list scan, one setup card, size, and the
  risk gate. Use when the user asks for the morning chain. A BLOCK writes
  no ticket. NSE and BSE only.
---

# Morning chain

The chain quotes the commands it calls. It does not invent a price. No step places an order.

Not investment advice.

## Steps

1. Put the session, a source, surveillance facts, the scan list, the setup name, the size pack, and the gate pack in one file. A ticket block is optional. Leave it out to stop after a PASS.

```json
{
  "source": "fixture:morning",
  "session_date": "2026-11-06",
  "setup": "orb",
  "surveillance": {"symbol": "RELIANCE", "exchange": "NSE", "series": "EQ", "session_date": "2026-11-06", "source": "fixture:surveillance"},
  "scan": {"source": "fixture:scan", "session_date": "2026-11-06", "min_delivery_pct": 50, "names": []},
  "setup_pack": {"symbol": "RELIANCE", "exchange": "NSE", "series": "EQ", "last": 114, "opening_range_high": 113, "opening_range_low": 111},
  "size": {"risk_inr": 1000, "lot_size": 1, "as_of": "2026-11-06"},
  "gate": {"min_r": 1.5, "daily_loss_inr": 0, "daily_loss_limit_inr": 5000, "planned_trades": 0, "max_planned_trades": 3, "data_as_of_ist": "2026-11-06T09:20:00+05:30", "now_ist": "2026-11-06T09:35:00+05:30", "max_age_minutes": 30, "costs_as_of": "2026-11-06"}
}
```

2. Run:

```
$env:PYTHONPATH = "src"
python -m indian_market.cli morning --fixture path\to\morning.json
```

`--demo` is `data/fixtures/morning.json`. A folder of exchange files is `session-pack` under official-files. This chain does not parse that folder.

## Output

```
Morning · SYMBOL
Chain: gate_pass | BLOCK | incomplete | the ticket status
Not investment advice. Nothing was sent to a broker.

| Field | Value | Session | Source |
| --- | --- | --- | --- |

Missing: one line for each item with ok false.
```

`chain_status` `gate_pass` means the gate passed and no ticket was requested. BLOCK means stop. Do not draft a ticket the command did not return. A name outside the watchlist, when `use_watchlist` is true, is a missing `scan_hit`.
