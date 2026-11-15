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

Run from the repository root with the environment activated.

| Command | What it does |
|---|---|
| `python src/clean.py` | Reads `data/raw/`, writes `data/clean/prices.parquet`. |
| `python src/features.py` | Reads prices, writes `data/clean/features_v1.parquet`. |
| `python -m pytest` | Checks the features and label for look-ahead. |
| `python src/download.py` | Re-downloads raw prices from Yahoo. Not needed: the raw files are in the repo so everyone uses identical data. |

To load the features in Python:

```python
import pandas as pd
features = pd.read_parquet("data/clean/features_v1.parquet")
```

Column meanings are in `reports/data_dictionary.md`. Known data problems are
in `reports/data_quality_report.md`.

## Status

Sprint 1: prices and features v1 are built. Models and regime detection start
in Sprint 2.
