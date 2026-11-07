# Charges

Rates live in `data/costs.json` with `effective_from` and `last_reviewed`. Run `python -m indian_market.cli costs`.

If `ok` is false, say the sheet is past its review horizon and do not use it to size a trade.

`stamp_duty` has `rate: null`. A stamp figure needs `buyer_state`. The Article 56A rate is uniform. The state is who receives it. An unknown state stays blank.

F&O STT rows dated 2026-04-01 record the reported Budget change (futures sell 0.05%, options premium sell 0.15%, exercise 0.15%). The source line says to confirm the Finance Act. Repeat that caveat when you quote them.

NSE equity, futures, and options transaction charges are on the sheet. BSE equity cash for groups A, B, and other non-exclusive scrips is `bse_txn_equity`. Other BSE groups, and BSE futures and options, stay blank.
