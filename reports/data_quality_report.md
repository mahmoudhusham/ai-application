# Data quality report - Sprint 1

Source: Yahoo Finance daily bars (`EURUSD=X`, `GBPUSD=X`, `USDJPY=X`),
downloaded once and stored in `data/raw/`. Period requested: 2000-01-01 to
2026-10-31. All numbers below are printed by `python src/clean.py` or can be
reproduced with `src/explore.py`.

## Rows

| Pair | Raw rows | First raw date | Clean rows | Removed |
|---|---|---|---|---|
| EURUSD | 5,946 | 2003-12-01 | 5,940 | 6 |
| GBPUSD | 5,958 | 2003-12-01 | 5,957 | 1 |
| USDJPY | 6,966 | 2000-01-03 | 5,942 | 1,024 |
| **Total** | **18,870** | | **17,839** | **1,031** |

## What was checked

| Check | Found | Action |
|---|---|---|
| Duplicate dates | 0 | none needed |
| Missing prices | 0 | none needed |
| Saturday or Sunday rows | 0 | none needed |
| Prices at or below 0 | 0 | none needed |
| Volume | always 0 | column dropped (FX has no central exchange) |
| Close spikes | 9 rows (EURUSD 5, USDJPY 4) | rows dropped |
| Impossible daily range | 2 rows (EURUSD 1, GBPUSD 1) | rows dropped |
| OHLC rules broken | 495 rows (EURUSD 128, GBPUSD 104, USDJPY 263) | repaired |
| Different start dates | USDJPY starts 4 years earlier | all pairs trimmed to 2003-12-01 (1,020 USDJPY rows) |

## Problems found and decisions

**Close spikes (9 rows, all in 2008).** The close jumps 3% to 18% and returns
the next day. All fall on the 8th of a month, and EURUSD and USDJPY are missing
most of August 2008. The likely cause is a day/month swap at the source (12
August stored as 8 December). Rule: drop a row when the close moves more than
3% and reverses by more than 3% the next day. Real events such as the Brexit
vote (-7.6%) do not reverse, so they are kept.

**Impossible range (2 rows, 2012-01-27).** EURUSD low of 0.76 and GBPUSD low of
0.64 on days that closed at 1.31 and 1.57. Rule: drop a row when high - low is
more than 15% of the close.

**OHLC rules broken (495 rows, 2.6%).** The open or close lies outside the
high-low range. The typical size is 0.01%, about one pip. Repair: set high to
the largest and low to the smallest of the four prices. No price is invented.

## Known limitations

- **Gaps are not filled.** Inventing prices would break the rule that a row
  only contains real information. Largest gaps: 18 and 8 days in August 2008
  (EURUSD, USDJPY), 6 days in January 2008 (GBPUSD), 5 days at Easter 2025
  (all pairs). Another 12 to 16 single weekdays are missing per pair.
- **Returns and labels across a gap cover more than one day.** 8 rows have a
  next row more than 4 days later.
- **30 of 5,963 dates do not have all three pairs.** Relevant for cross-pair
  features in Sprint 2.
- **The spike rule uses the next day's close** to decide whether a row is an
  error. It removes vendor errors and is not a model feature, but it is
  hindsight.
- **One suspicious value is left in:** USDJPY low on 2024-12-25 is 7% below a
  bar whose open and close are equal. It is under the 15% limit.
- **Some misdated 2008 rows may remain** where the wrong price was within 3%
  of the right one.
- **36 flat bars** (high equals low) remain, mostly on holidays.
- **Yahoo FX prices are indicative quotes**, not exchange trades. Fine for an
  educational project.

## Features and label

`features_v1.parquet` has 17,776 rows and no missing values. Share of "up"
days: EURUSD 49.5%, GBPUSD 49.6%, USDJPY 51.9%. The label is close to balanced,
so a model that always predicts one direction scores about 50%.

Look-ahead is checked by `python -m pytest` (4 tests, all passing). The key
test rebuilds the features from prices that stop in June 2015 and confirms
every feature value on the earlier dates is unchanged. A feature that used
future data would change. The test was confirmed to fail on two deliberately
leaky features.
