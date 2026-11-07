---
name: post-result
description: >
  Builds a next-session gap setup card after a results date already on disk
  for one NSE or BSE symbol. Use when the user asks for a post-result setup.
  The results session itself stays blocked. NSE and BSE only.
---

# Post result

The session has to be the next trading session after `results_date`. The results day itself is blocked. This card does not recommend an option structure.

Not investment advice. This is not an order.

## Steps

1. Carry `results_date`, session, previous close, last, and `min_gap_pct`. Note a concall line and an ex-date only when the pack has them.

```json
{
  "symbol": "RELIANCE",
  "exchange": "NSE",
  "series": "EQ",
  "session_date": "2026-11-06",
  "source": "fixture:post",
  "results_date": "2026-11-05",
  "prev_close": 100,
  "last": 104,
  "min_gap_pct": 1,
  "surveillance": {"clearance": "clear", "source": "fixture:surveillance", "session_date": "2026-11-06"}
}
```

2. Run:

```
$env:PYTHONPATH = "src"
python -m indian_market.cli setup --name post --fixture path\to\setup.json
```

`--demo` is `data/fixtures/setup_post.json`. That session is the Friday after a Thursday result. Do not move the demo onto the Muhurat session.

## Output

```
Setup · post_result · SYMBOL
Status: ready | blocked | invalid | incomplete
Not investment advice.

| Field | Value | Session | Source |
| --- | --- | --- | --- |

Missing: one line for each item with ok false.
```

A gap up is long. A gap down is short. Invalidation is the previous close. A gap inside `min_gap_pct` is `invalid`. A missing concall or ex-date stays missing.
