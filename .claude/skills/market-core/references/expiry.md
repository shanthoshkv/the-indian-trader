# Expiry

As of November 2026. One weekly index contract per exchange since 20 November 2024. From 1 September 2025 the weekdays are:

| Contract | Exchange | Weekly | Monthly |
| --- | --- | --- | --- |
| Nifty | NSE | Tuesday | Last Tuesday |
| Bank Nifty, Fin Nifty, Midcap Select | NSE | None | Last Tuesday |
| Stock futures and options | NSE | None | Last Tuesday |
| Sensex | BSE | Thursday | Last Thursday |
| Bankex | BSE | None | Last Thursday |

A holiday moves that expiry to the previous trading session. Stock contracts are physically settled. Index contracts are cash settled.

Run `python -m indian_market.cli expiry NIFTY --on YYYY-MM-DD` and quote `weekly` and `monthly` from the JSON. Bank Nifty returns `weekly: null` on purpose.

Do not tell the user that Bank Nifty still expires every Thursday. That schedule ended in 2024, and the NSE weekday moved from Thursday to Tuesday in 2025.
