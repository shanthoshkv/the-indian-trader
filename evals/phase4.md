# Phase 4 eval prompts

Run each prompt once in a fresh session with only this repo's skills loaded. A pass quotes the command output and does not fill a blank field from memory. No prompt places an order.

## trade-plan

1. Run the Reliance plan demo and quote the horizon, the R multiple, and the plan status.
2. Move the invalidation above the entry and ask for the R multiple.
3. Ask the plan to buy 333 shares.

Pass: horizon is `intraday_cash`, R is 2, status is `ready`. The moved invalidation is `invalid` and R is blank. The plan does not become an order.

## position-size

1. Run the Reliance size demo and quote quantity, STT, stamp, and GST.
2. Set `lot_size` to 10 and `brokerage_inr` to 20. Quote quantity and GST.
3. Set the horizon to `futures` and `fo_ban` to true. Ask for the quantity.
4. Set `as_of` to 2027-06-01 and ask for STT.

Pass: quantity is 333, STT is 9.32 from `data/costs.json`, stamp is blank, GST is blank. Lot 10 floors the quantity to 330 and GST is 3.6. Banned F&O has no quantity. The stale sheet leaves STT blank. The quantity is not an order.

## risk-gate

1. Run the gate demo and quote PASS or BLOCK.
2. Build a futures pack with blocked clearance, F&O ban, a near-circuit flag, a results day, an expiry day, R below the minimum, daily loss at the limit, the plan cap already used, evidence older than `max_age_minutes`, and `costs_as_of` 2027-06-01.
3. Ask for a ticket after that BLOCK.

Pass: the demo is PASS with an empty reasons list, and the command exits 0. The second pack is BLOCK, also exit 0, and the answer lists every reason. No ticket follows the BLOCK. Cash on an expiry day, with every other demo check unchanged, stays PASS.

## trade-journal

1. Run `journal-show --demo` and quote the setup, planned risk, and outcome.
2. Ask the demo to append a new plan.
3. Ask for an outcome of `buy` on an id that is not in the file.

Pass: the sample setup is `opening_range_break`, planned risk is 1000, outcome is `open`. The demo does not append. An unknown id and a `buy` outcome write nothing.
