# Data dictionary

Covers the two shared files built by the data pipeline. Pairs: EURUSD, GBPUSD,
USDJPY. One row per trading day per pair ("long" format).

**What a day means.** Prices come from Yahoo Finance daily bars. A bar runs
from midnight to midnight London time. "Close of day D" is therefore midnight
London time at the end of D, for all three pairs.

**Golden rule.** Every feature on a row dated D uses only prices up to and
including the close of D. Only the label looks forward, to the next row.

## prices.parquet

Location: `data/clean/prices.parquet`. Built by `python src/clean.py`.
17,839 rows, 2003-12-01 to 2026-10-30.

| Column | Type | Meaning |
|---|---|---|
| `date` | date | Trading day (London time). Monday to Friday only. |
| `pair` | text | `EURUSD`, `GBPUSD` or `USDJPY`. |
| `open` | number | First price of the day. |
| `high` | number | Highest price of the day. Always >= open, close and low. |
| `low` | number | Lowest price of the day. Always <= open, close and high. |
| `close` | number | Last price of the day. |

A pair name reads "base then quote": EURUSD = 1.10 means one euro costs 1.10
dollars. USDJPY = 157 means one dollar costs 157 yen.

## features_v1.parquet

Location: `data/clean/features_v1.parquet`. Built by `python src/features.py`.
17,776 rows, 2003-12-29 to 2026-10-29. No missing values.

All features are computed separately for each pair. All are ratios or
percentages, so they are comparable between EURUSD (about 1.1) and USDJPY
(about 157).

| Column | Meaning | Formula | Looks back |
|---|---|---|---|
| `date` | Trading day | | |
| `pair` | Currency pair | | |
| `ret_1d` | Today's return | close / previous close - 1 | 1 day |
| `ret_lag1` | Yesterday's return | `ret_1d` from 1 row earlier | 2 days |
| `ret_lag2` | Return 2 days ago | `ret_1d` from 2 rows earlier | 3 days |
| `ret_lag3` | Return 3 days ago | `ret_1d` from 3 rows earlier | 4 days |
| `ret_lag5` | Return 5 days ago | `ret_1d` from 5 rows earlier | 6 days |
| `ma_5_ratio` | Close against its 5-day average | close / mean of last 5 closes - 1 | 5 days |
| `ma_20_ratio` | Close against its 20-day average | close / mean of last 20 closes - 1 | 20 days |
| `rsi_14` | Relative Strength Index, 0 to 100 | 100 - 100 / (1 + average gain / average loss), Wilder smoothing over 14 days | all history, mostly the last ~14 days |
| `atr_14_pct` | Average True Range as a fraction of close | Wilder average over 14 days of the true range, divided by close | all history, mostly the last ~14 days |
| `vol_20` | Rolling volatility | standard deviation of the last 20 `ret_1d` values | 21 days |
| `next_day_up` | **Label.** 1 if the next row's close is higher than this row's close, else 0 | next close > close | looks FORWARD 1 row |

Notes:

- **True range** for a day is the largest of: high - low, |high - previous
  close|, |low - previous close|.
- **Wilder smoothing** is an exponential average where the newest value gets
  weight 1/14 and the previous average gets weight 13/14.
- **RSI reading:** above 70 is usually called overbought, below 30 oversold.
- **Label ties:** if the next close equals today's close the label is 0
  (77 rows across all pairs).
- **Dropped rows:** the first 20 rows of each pair (not enough history for the
  20-day windows) and the last row of each pair (no next day, so no label).
- **"Next row" is the next available trading day.** After a data gap this can
  be more than one calendar day later. See the data quality report.
