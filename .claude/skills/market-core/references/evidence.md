# Evidence

Every number in a user-facing note comes from one of these objects. A blank `value` with `ok: false` stays blank.

```json
{
  "ok": true,
  "symbol": "RELIANCE",
  "exchange": "NSE",
  "series": "EQ",
  "field": "close",
  "value": 108.0,
  "unit": "INR",
  "session_date": "2026-11-05",
  "as_of_ist": "2026-11-05T18:10:00+05:30",
  "source": "fixture:nse-cm-bhavcopy",
  "freshness": "fixture"
}
```

`freshness` is one of `live_snapshot`, `previous_session`, `delayed_vendor`, `filing`, `fixture`, `unavailable`.

FII and DII cash figures are `previous_session` during the day. Delivery percent during the session is the previous bhavcopy. A `fixture` source is a sample. Say so in the first line of the note.

Yahoo `.NS` and `.BO` daily bars may be used only as `delayed_vendor` OHLC when no bhavcopy is available. They are not a source for open interest, delivery, ban status, or corporate actions.
