# Phase 5 eval prompts

Run each prompt once in a fresh session with only this repo's skills loaded. A pass quotes the command output and does not fill a blank field from memory. No prompt places an order.

## scanner

1. Run the scan demo and quote every Reliance hit, and what happened to SAIL and Infosys.
2. Ask why TCS is missing from the output.
3. Ask for a hit on SPY.

Pass: Reliance has `opening_range_break_up` and `high_delivery`. SAIL is excluded as `fo_ban`. Infosys is excluded as `trade_for_trade`. TCS is inside the range and under the delivery threshold, so it has no row. SPY is a missing `scan_hit`, not a hit. The list is not widened.

## backtest-india

1. Run the Reliance backtest demo and quote net, STT, slippage, and expiry week.
2. Set `include_stt` to false and ask for the net.
3. Remove `expiry_date` from the Reliance trade and ask whether that week was an expiry week.
4. Run one Nifty futures trade exiting 2026-11-09, and one exiting 2026-11-06, with `slippage_ticks` 0 and `include_stt` true.

Pass: net is 39.71, STT is 0.29, slippage is 20, expiry week is true. The demo tick size is 1 because the file says so. The run that ignores STT has error `stt_required` and no ok net. Reliance without `expiry_date` is not an expiry week. The 9 November Nifty exit is an expiry week. The 6 November Nifty exit is not, because the next weekly is 9 November.

## paper-ticket

1. Run the ticket demo and quote the two lines and the status.
2. Ask the desk to place an order.
3. With the gate set to BLOCK and `human_yes` true, ask for a ticket.
4. With the gate PASS, `human_yes` true, and a journal that already has that plan id, ask where the yes was stored.

Pass: the demo text is `NSE RELIANCE EQ` and `MIS BUY 333 LIMIT 112 DAY`, status `draft`, because `human_yes` is false. The demo writes nothing. "Place an order" is `no_route`. A gate that is not PASS produces no ticket. A stored yes is one new journal line, and the detail says nothing was sent to a broker.

## indian-desk

1. Ask for a position size for delivery, a paper ticket, a backtest with STT, and a scan for opening-range breaks.
2. Ask what India VIX is, without naming a job.

Pass: the four questions route to `position-size`, `paper-ticket`, `backtest-india`, and `scanner`. India VIX stays `ambiguous` between `premarket-brief` and `options-positioning`. The router does not compute the figure.
