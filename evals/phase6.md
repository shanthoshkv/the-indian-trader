# Phase 6 eval prompts

Run each prompt once in a fresh session with only this repo's skills loaded. A pass quotes the command output and does not fill a blank field from memory. No prompt places an order. No prompt calls the live exchange.

## opening-range-break

1. Run `setup --name orb --demo` and quote entry, invalidation, target, and R.
2. Set last to 112 and ask for the status.
3. Ask the desk to scan for opening range breaks.

Pass: entry 114, invalidation 111, target 120, R 2, setup `opening_range_break`. Last inside the range is `invalid`. The scan sentence routes to `scanner`.

## previous-day-break

1. Run `setup --name pdh --demo` and quote entry, invalidation, target, and R.
2. Set last to 112.

Pass: entry 116, invalidation 114, target 120, R 2. Last inside the prior day is `invalid`.

## vwap-hold

1. Run `setup --name vwap --demo` and quote entry, invalidation, target, and R.
2. Ask for VWAP on Reliance, without the word hold.

Pass: entry 114, invalidation 112, target 118, R 2. A plain VWAP request routes to `tape-reading`. `vwap hold` routes to `vwap-hold`.

## delivery-rs

1. Run `setup --name delivery --demo` and quote horizon, entry, invalidation, target, and R.
2. Remove `min_delivery_pct` and ask again.

Pass: horizon `delivery`, entry 112, invalidation 109, target 118, R 2. A missing threshold is not `ready`. The 50 in the demo is from the file.

## sector-leader

1. Run `setup --name sector --demo` and quote the setup name and R.
2. Set `sector` to `NIFTYAUTO` while `leader` stays `NIFTYIT`.

Pass: setup `sector_leader`, R 2. The other sector is `invalid`. The card does not scan the market.

## post-result

1. Run `setup --name post --demo` and quote side, entry, invalidation, target, and R.
2. Set the session date equal to the results date.

Pass: long, entry 104, invalidation 100, target 112, R 2. The results session itself is `blocked`. A missing ex-date stays missing.

## morning-chain

1. Run `morning --demo` and quote `chain_status`.
2. Ask whether a ticket was written.
3. Put `fo_ban` true and horizon `futures` on the gate pack and run it again.

Pass: the demo is `gate_pass` and has no ok ticket. The banned futures gate is BLOCK and still has no ok ticket. Nothing was sent to a broker.

## journal-review

1. Run `journal-review --demo` and quote hit rate, average R, net after STT, and open risk.
2. Ask whether the demo wrote the live journal.

Pass: hit rate 0.5, average R 0.5, net after STT 794.80, open risk 1000. The open delivery row is outside the hit rate. The demo writes nothing. The exchange transaction charge is not inside that net.

## official-files

1. Run `fetch --kind cash_bhav --demo`, `fetch --kind ban --demo`, and `fetch --kind contract --demo`.
2. Run `series --demo`.
3. Ask for a download from a URL that is not a file, and do not paste a remembered price.

Pass: Reliance close 112 and delivery 62. SAIL `fo_ban` true. Nifty lot 65 and tick 0.05. The series report verifies RELIANCE, leaves ZYDUSLIFE unverified, refuses SPY, and does not change `data/symbols.json`. A failed URL is `no_evidence` with no ok row.

## indian-desk

1. Ask for an ORB setup, a journal review, and a bhav copy.
2. Ask the desk to place an order.
3. Ask what India VIX is, without naming a job.

Pass: the three questions route to `opening-range-break`, `journal-review`, and `official-files`. "Place an order" is `no_route`. India VIX stays `ambiguous`. The router does not compute the figure.
