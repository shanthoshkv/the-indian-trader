# Sessions

Times are IST. India does not observe daylight saving.

Ordinary day, equity and the current-month futures pre-open, as revised from 7 September 2026:

| Clock | Phase |
| --- | --- |
| Before 09:00 | Closed |
| 09:00–09:05 | Pre-open, limit and market orders |
| 09:05–09:10 | Pre-open, limit orders only. Random close in the last two minutes |
| 09:10–09:12 | Matching |
| 09:12–09:15 | Buffer |
| 09:15–15:30 | Continuous |
| After 15:30 | Closed |

Weekends are closed. Weekday holidays are in `data/holidays.json`, taken from NSE circular NSE/CMTR/71775 (12 December 2025). 15 January 2026 is on the BSE list and is not in that NSE extract, so the calendar treats it as BSE-only.

Muhurat trading on 8 November 2026 (Diwali Laxmi Pujan, a Sunday): pre-open from 14:05, continuous equity from 14:20 to 15:30. Source: NSE/CMTR/76941. The command `session` returns `muhurat` inside that window.

The command output is the phase to quote. If a newer circular disagrees with this page, trust the circular and update `data/holidays.json`.
