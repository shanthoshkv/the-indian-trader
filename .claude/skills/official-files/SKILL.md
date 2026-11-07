---
name: official-files
description: >
  Parses an NSE or BSE file the user already has, including a session folder,
  and can try one public URL. Use when the user asks for a bhav copy, an
  official file, a session pack, or a series report. A failed download stays
  blank. NSE and BSE only.
---

# Official files

A field is filled only from the file the command parsed. Yahoo bars stay delayed OHLC and are not a source for open interest, delivery, ban, or corporate actions.

Not investment advice. Nothing here places an order.

## Steps

1. To parse a file already on disk:

```
$env:PYTHONPATH = "src"
python -m indian_market.cli fetch --kind cash_bhav --session 2026-11-06 --file path\to\bhav.csv
python -m indian_market.cli fetch --kind ban --demo
python -m indian_market.cli fetch --kind contract --demo
```

`--demo` reads the fixture for `cash_bhav`, `ban`, `contract`, `delivery`, or `constituents`. Other kinds need `--file`. Kinds also include `fo_bhav`, `flows`, `announcements`, `bulk_deals`, `block_deals`, `asm`, `gsm`, `esm`, `mwpl`, `shareholding`, and `pledge`. A blank pledge cell is not zero. A constituent weight stays blank when the file has none. There is no list of index members in this pack.

2. A session folder parses each known file that is present and leaves the rest blank. It does not run the morning chain.

```
python -m indian_market.cli session-pack --dir data\sessions\2026-11-06
python -m indian_market.cli session-pack --demo
```

`--demo` is `data/fixtures/session_sample`. One file still uses `fetch`. The desk label for a session folder stays `fetch`.

3. A public URL is optional. Pass `--url`. If the download fails, leave the field blank. Do not retype the figure from memory.

```
python -m indian_market.cli fetch --kind cash_bhav --session 2026-11-06 --url https://example.invalid/bhav.csv
```

4. A series report counts verified, unverified, and refused rows. It does not rewrite `data/symbols.json`.

```
python -m indian_market.cli series --demo
python -m indian_market.cli series --file path\to\series.csv
```

## Output

```
Official file · kind · session
Not investment advice.

| Symbol | Field | Value | Source |
| --- | --- | --- | --- |

Missing: one line for each item with ok false.
```

Delivery percent from a cash file is a previous-session figure. A ban row is `fo_ban`. Lot size, tick, and freeze quantity come from the contract file. Do not invent a BSE scrip code the report did not verify.
