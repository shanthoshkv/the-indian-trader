# Desk and book eval prompts

Run each prompt once in a fresh session with only this repo's skills loaded. A pass quotes the command output and leaves a missing field blank.

Do not rewrite `evals/phase1.md`. These checks are for the router and the 0.4.0 commands.

## Routes

1. "trading mandate" routes to `mandate`. Command is `none`.
2. "investment thesis" routes to `thesis-memo`. Command is `none`.
3. "short case" routes to `short-case`. Command is `none`.
4. "book risk" routes to `book-risk`. Command is `book`.
5. "pair trade" routes to `pair-note`. Command is `none`.
6. "investment committee" routes to `ic-note`. Command is `none`.
7. "risk gate" routes to `risk-gate`.
8. "place an order" is `no_route`.
9. "what is india vix" is `ambiguous`.
10. "session pack" routes to `official-files`. Command stays `fetch`.

These sentences keep their earlier winners: "scan for opening range breaks" is `scanner`. "orb setup" and "opening range strategy" are `opening-range-break`. "vwap" is `tape-reading`. "vwap hold" is `vwap-hold`. "delivery and relative strength" is `delivery-rs`. "journal" is `trade-journal`. "journal review" is `journal-review`.

Bare "thesis", "short", "pair", "risk", and "mandate" are not routes.

## check-brief

1. `check-brief --kind thesis` on `data/fixtures/thesis_ok.md` passes.
2. `check-brief --kind short` on `data/fixtures/short_ok.md` passes.
3. `check-brief --kind ic` on `data/fixtures/ic_ok.md` passes. The decision heading is empty.
4. `data/fixtures/ic_bad.md` fails because the decision line is not empty.
5. A bullet that starts with buy or sell fails. The word buyback does not.

## Mandate on the gate

1. `gate --demo` stays PASS. The demo pack has no mandate.
2. `gate --demo --mandate data/mandate.json` stays PASS. Null caps do not block.
3. A pack whose horizon is outside the mandate horizon list is BLOCK. A short when `allow_short` is false is BLOCK. Series SM, ST, or SZ when `allow_sme` is false is BLOCK. Series BE is not an SME block. Muhurat when `allow_muhurat` is false is BLOCK. A plan loss limit above the mandate cap is BLOCK.
4. Nobody overrides a BLOCK. The mandate skill does not size.
