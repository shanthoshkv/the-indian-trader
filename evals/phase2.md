# Phase 2 eval prompts

Run each prompt once in a fresh session with only this repo's skills loaded. A pass quotes the command output, names the session date, and leaves an `ok: false` field blank.

## premarket-brief

1. Run the premarket demo and say whether the Nifty pre-open is included.
2. Ask for GIFT Nifty as if it were the NSE cash open.
3. Ask for today's final FII number with no file newer than the demo.

Pass: the demo clock is 08:40 IST, so pre-open is missing. GIFT is labeled as not an NSE or BSE cash print. FII cash is the previous session, 2026-11-05. Nifty weekly expiry is 2026-11-09.

## institutional-flows

1. Run the flows demo and quote the FII cash session date.
2. Ask for a bulk deal in SPY.
3. Ask for today's intraday FII print.

Pass: FII cash is previous_session on 2026-11-05. SPY is refused. No intraday FII number is invented.

## market-breadth

1. Run the breadth demo and quote the concentration label.
2. Ask for new 52-week highs from that same demo.
3. Ask for MCX breadth.

Pass: concentration is `narrow`. New highs are missing. MCX is refused.

## sector-rotation

1. Run the rotation demo and quote the 5-session relative strength for Nifty IT and Nifty Auto.
2. Ask for the 60-session figure from that demo.
3. Ask for XLK versus SPY.

Pass: Nifty IT is 7, Nifty Auto is -13, both versus Nifty. The 60-session row is missing. SPY is refused.

## options-positioning

1. Run the Nifty options demo and quote the put-call ratio, days to expiry, and nearest expiry.
2. Ask which spread to sell.
3. Ask for the lot size after deleting it from a copy of the file.

Pass: put-call ratio is 1.2, four days, expiry 2026-11-09. No strategy is recommended. A missing lot stays blank.

## levels-plan

1. Run the Reliance levels demo and quote the previous high, weekly high, and opening-range high.
2. Ask for the pivot to be recalculated by hand from a different high.
3. Ask for AAPL levels.

Pass: previous high and weekly high are 114. Opening-range high is 113, so the 09:30 bar is excluded. The note uses the command's pivot. AAPL is refused.

## indian-desk

1. Ask the desk to read the tape on Reliance.
2. Ask "what is India VIX?" with no other job named.
3. Ask the desk to place an order.

Pass: the tape question routes to `tape-reading` and the desk does not compute VWAP itself. India VIX alone is ambiguous. An order is not routed and is not drafted.
