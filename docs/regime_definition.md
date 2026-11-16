# Regime definition (v0): trending vs ranging

Owner: Kur. Status: DRAFT, to be agreed by the team at the Sprint 1 mid-sprint checkpoint.

## Definition

| Regime | Meaning | Measurable rule (v0) |
|---|---|---|
| TRENDING | Price moves steadily in one direction | ADX(14) >= 25 |
| RANGING | Price bounces sideways in a band | ADX(14) < 25 |

- **ADX** (Average Directional Index, Wilder, 14 days) measures how strong a trend is, 0 to 100. It does not say
  whether the trend is up or down, only how directional the market is. 25 is the classic textbook cut-off.
- Computed per pair from daily high, low and close. Needs about 28 days of warm-up, so the first rows of each pair
  have no label and are not exported.
- **No look-ahead:** the label dated D uses prices up to the close of day D only. It describes the market today and
  is used as a filter for the prediction made for D+1. (Unit test: removing future data does not change past labels.)

## Output: `regimes_v0.csv`

`date, pair, regime, trend_strength` where `regime` is TRENDING or RANGING and `trend_strength` is the ADX value.
Same column names will be kept in `regimes_v1.csv` (Sprint 2).

## Alternatives we will compare in Sprint 2

- Moving-average slope (for example 50-day average, change over 10 days, divided by ATR): trending if the slope is large.
- Data-driven: Hidden Markov Model or clustering on returns and volatility (regime detector v1).

## Known weaknesses (to report honestly)

- ADX lags: it confirms a trend after it has started, and stays high a little after it ends.
- The 25 threshold is a convention, not a law. Sprint 2 may tune it on validation data only.
- Labels can flicker around 25. If the backtest shows too many regime switches we can add a buffer
  (for example enter TRENDING at 27, leave at 23).

## Backtest conventions (needed from the team)

- BUY = +1, SELL = -1, HOLD = flat. A signal at the close of D earns the return from D to D+1.
- Cost: spread paid on every position change, half per side (round trip = one full spread).
- Assumed spreads in pips (to confirm with the team): EURUSD 1.0, GBPUSD 1.5, USDJPY 1.0. JPY pip = 0.01.
