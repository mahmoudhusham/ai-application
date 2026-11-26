# Welders - FX Market Direction & Regime Predictor

A university project that predicts the next-day direction of three currency
pairs (EURUSD, GBPUSD, USDJPY) from daily prices, detects whether the market
is trending or ranging, and combines both into BUY / SELL / HOLD signals.

Educational only. Nothing here places trades.

## Pipeline

```
prices -> clean + features -> direction model --\
                           -> regime detector ---+-> signal generator -> signals file
```

| Part                                  | Owner   |
|---------------------------------------|---------|
| Data pipeline, features, signal export | Mahmoud |
| Direction models                       | Khatab  |
| Regime detection, backtesting          | Kur     |

## Setup

Requires Python 3.12.

```powershell
git clone https://github.com/mahmoudhusham/ai-application
cd ai-application
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Your prompt should start with `(.venv)` after activating. On macOS or Linux,
activate with `source .venv/bin/activate` instead.

## Where files live

| Folder        | Contents                                                    |
|---------------|-------------------------------------------------------------|
| `data/raw/`   | Prices as downloaded. Never edited by hand.                 |
| `data/clean/` | `prices.parquet` and `features_vN.parquet`, built by `src/`. |
| `src/`        | Pipeline code.                                              |
| `tests/`      | pytest tests.                                               |
| `reports/`    | Data dictionary and data quality report.                    |

## How to run

Run every command from the repository root with the environment activated.
Run the steps in this order: each one reads files made by earlier steps.

| Step | Command | Owner | Writes |
|---|---|---|---|
| 1 | `python src/clean.py` | Mahmoud | `data/clean/prices.parquet` |
| 2 | `python src/features.py` | Mahmoud | `data/clean/features_v1.parquet` |
| 3 | `python src/models/direction.py` | Khatab | `predictions/predictions_v1.csv`, `reports/validation_table.csv` |
| 4 | `python -m src.regime.rule_based` | Kur | `data/clean/regimes_v0.csv` |
| 5 | `python -m src.backtest.run --regimes data/clean/regimes_v0.csv --start 2020-01-01 --end 2022-12-31` | Kur | `reports/backtest_results.csv`, `reports/figures/equity_curves.png` |
| 6 | `python -m src.regime.plot_regime --pair EURUSD` | Kur | `reports/figures/regime_EURUSD.png` |
| - | `python -m pytest` | all | runs all tests |

Always backtest with `--start 2020-01-01`: earlier predictions are on the
model's own training data and look better than they are.

`python src/download.py` re-downloads raw prices from Yahoo. It is not needed:
the raw files are in the repo so everyone uses identical data.

To load the features in Python:

```python
import pandas as pd
features = pd.read_parquet("data/clean/features_v1.parquet")
```

Column meanings are in `reports/data_dictionary.md`. Known data problems are
in `reports/data_quality_report.md`. The model results are in
`reports/direction_report.md` and the regime rule in `docs/regime_definition.md`.

## Status

Sprint 1: prices, features v1, a first direction model, a rule-based regime
labeller and a backtester are built and run end to end.
