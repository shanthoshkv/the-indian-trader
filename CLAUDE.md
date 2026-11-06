# The Indian trader

Skills in this repo analyze NSE and BSE only: equity cash, equity indices, and the equity and index futures and options on those two exchanges. MCX, NCDEX, crypto, and foreign listings are out. Say so and stop.

This is not a SEBI-registered research service and not investment advice. No skill places an order.

Numbers come from `python -m indian_market.cli` or from a file that command has checked. A field with `ok: false` stays blank. A `fixture` source is a sample. FII, DII, and delivery figures during the session are previous-session figures.

From the repo root:

```
$env:PYTHONPATH = "src"
python -m indian_market.cli resolve RELIANCE
```

| Ask | Skill |
| --- | --- |
| Timings, expiry, charges, which exchange | market-core |
| Ban, ASM, GSM, trade-for-trade | surveillance-check |
| What the company is, filings, peers | market-research |
| Price, delivery, relative strength, buildup | market-analysis |
| Auditable SWOT | swot-analysis |
| VWAP, opening range, previous day high and low | tape-reading |

Phases 2 through 5 are specified in README.md and are not implemented. Do not invent a pre-market brief, an FII print, an option chain, or an order.
