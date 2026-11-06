# Charges

Rates live in `data/costs.json` with `effective_from` and `last_reviewed`. Run `python -m indian_market.cli costs`.

If `ok` is false, say the sheet is past its review horizon and do not use it to size a trade.

Stamp duty has `rate: null` because it depends on the state. Do not invent one national stamp rate.

F&O STT rows dated 2026-04-01 record the reported Budget change (futures sell 0.05%, options premium sell 0.15%, exercise 0.15%). The source line says to confirm the Finance Act. Repeat that caveat when you quote them.

Exchange transaction charges are not in the file. They change by circular. Leave them out until a reviewed row exists.
