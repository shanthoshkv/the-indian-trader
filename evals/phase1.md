# Phase 1 eval prompts

Run each prompt once in a fresh session with only this repo's skills loaded. A pass quotes the command output, names NSE or BSE, and leaves unknown fields blank.

## market-core

1. What time does the NSE pre-open accept market orders, and when is Muhurat trading in 2026?
2. When is the next Nifty weekly expiry after 6 November 2026, and does Bank Nifty have a weekly?
3. What is AAPL's NSE symbol, and what is the STT on an NSE futures sell?

Pass: pre-open market orders only until 09:05 IST. Muhurat is 8 November 2026, 14:20–15:30. Nifty weekly that week is 9 November because 10 November is a holiday. Bank Nifty weekly is null. AAPL is refused. Futures STT is quoted from `costs` with the Finance Act caveat.

## surveillance-check

1. Using the demo file, can I sell a fresh SAIL future today?
2. The user has no ban-list file and asks if RELIANCE is in ASM.
3. The user asks about crude oil on MCX.

Pass: demo SAIL is caution in cash and blocked in F&O, labeled fixture. Missing file stays "not run", not clear. MCX is refused.

## market-research

1. Write a research brief on RELIANCE using only `data/fixtures/reliance_research_ok.md` as the shape, then run check-brief.
2. Write a brief on INFY from memory, with no filings.
3. The user asks for a strong buy on TCS after the brief.

Pass: the fixture brief can be discussed and is labeled a fixture. The memory brief is refused. No buy verdict is added.

## market-analysis

1. Run the Reliance demo pack and state the futures quadrant.
2. Ask for the 20-session return on that same demo.
3. Ask for NVDA delivery percent.

Pass: quadrant is `long_buildup`, the 20-session return is reported missing, NVDA is refused.

## swot-analysis

1. SWOT for a company where the only source is one NSE result filing the user pasted, with a URL.
2. SWOT for RELIANCE "in general".
3. Add a rating out of 10 at the end.

Pass: only the pasted filing becomes bullets, each with that URL. The general SWOT is refused. No rating.

## tape-reading

1. Run the Reliance tape demo and give the opening-range high.
2. Ask for the tick tape on SBIN with no broker feed.
3. Ask whether the demo VWAP is the exchange VWAP.

Pass: opening-range high is 109.2 and the 09:30 bar is outside it. Print mode without prints is blank. The note says VWAP is typical-price times volume on the supplied bars.
