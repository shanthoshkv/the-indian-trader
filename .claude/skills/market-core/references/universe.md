# Universe

This pack covers NSE equity cash (EQ, BE, SME series), BSE equity cash including BSE SME, NSE and BSE equity indices, and the equity and index futures and options on those two exchanges.

A name listed on both exchanges defaults to NSE EQ. `RELIANCE.BO`, a 6-digit scrip code, or an explicit BSE request selects BSE.

Outside the pack: MCX, NCDEX, crypto, US listings, and GIFT Nifty treated as an NSE cash print. NSE currency and NSE commodity derivatives are out of this version.

The starter book is `data/symbols.json`. It is a reviewed subset, not the full security master. Lot size and tick size come from the day's contract or security file when a later fetcher supplies them. Until then, do not invent a lot size.

Tick schedule used when the security file is absent, from the April 2025 cash and stock-futures revision: below 250 use 0.01, 250 to 1,000 use 0.05, 1,000 to 5,000 use 0.10, 5,000 to 10,000 use 0.50, 10,000 to 20,000 use 1.00, above 20,000 use 5.00. The security file wins when a series differs.
