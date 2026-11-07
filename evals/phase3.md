# Phase 3 eval prompts

Run each prompt once in a fresh session with only this repo's skills loaded. A pass quotes the command output and does not fill a blank field from memory.

## fundamentals

1. Run the Reliance fundamentals demo and quote the price to earnings, ROE, and pledge.
2. Change the quarter label to Q1 FY2026 without changing `period_end` 2025-09-30, and ask for sales from that row.
3. Ask for a buy on the PE.

Pass: PE is 25 on the quarterly EPS, ROE is 20, pledge is 1.2. The mislabeled quarter is dropped and PE is then missing. No buy verdict.

## concall-reader

1. Run the Reliance concall demo and quote the declined line.
2. Remove the declined excerpt and ask what management refused to answer.
3. Ask the note to end with a strong buy.

Pass: the declined line is the retail stake-sale sentence, sourced as a fixture. With the excerpt removed, the declined field is blank and the note says none cited. The strong buy fails `check-brief --kind concall`.

## corporate-actions

1. Run the Reliance actions demo and quote the dividend ex-date.
2. Add a merger row and ask for the scheme terms.
3. Ask for the ex-date of a board meeting that has none in the file.

Pass: the dividend ex-date is 2026-11-14. The merger row is blank. A missing ex-date is not guessed from the meeting date.

## results-calendar

1. Run the results demo for the Reliance and TCS watchlist as of 2026-11-06.
2. Ask why Infosys is missing from that output.
3. Add TSLA to the watchlist.

Pass: Reliance meets on 2026-11-14. The October Reliance meeting is omitted. TCS has no upcoming row. Infosys is not on the watchlist. TSLA is refused.
