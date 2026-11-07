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
| Premarket brief, GIFT Nifty, morning expiries | premarket-brief |
| FII, DII, participant open interest, bulk and block deals | institutional-flows |
| Advance and decline, new highs, concentration | market-breadth |
| Sector versus Nifty or Sensex | sector-rotation |
| Put-call ratio, listed expiry, lot and freeze from the file | options-positioning |
| Pivot, weekly range, computed levels | levels-plan |
| Which skill should answer | indian-desk |
| Results numbers, pledge, shareholding, fiscal year | fundamentals |
| Concall guidance, capex, declined answers | concall-reader |
| Dividend, split, bonus, ex-date | corporate-actions |
| Upcoming results for a watchlist | results-calendar |
| Trade plan, R multiple | trade-plan |
| How many shares, rupee risk | position-size |
| PASS or BLOCK | risk-gate |
| Journal, setup, outcome | trade-journal |
| Scan a named list | scanner |
| Backtest with STT and slippage | backtest-india |
| Paper ticket, manual ticket | paper-ticket |
| Opening range strategy, ORB setup | opening-range-break |
| Previous day break | previous-day-break |
| VWAP hold | vwap-hold |
| Delivery and relative strength, as a setup | delivery-rs |
| Sector leader setup | sector-leader |
| Post-result setup | post-result |
| Morning chain | morning-chain |
| Journal review, hit rate | journal-review |
| Bhav copy, official file, series report | official-files |

`fetch` parses a file you have, or tries one public URL. A failed download leaves the field blank. Do not fill it from memory. A command with no fixture leaves the field blank. Do not invent an order. A journal line, a scan row, or a ticket exists only when that command wrote it. BLOCK stops the chain. A backtest that ignores STT has no net. The exchange transaction charge is not inside that net. Stamp duty and the BSE transaction rate stay blank.
