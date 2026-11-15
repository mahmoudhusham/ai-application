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
git clone https://github.com/mahmoudhusham/ai-applicaion
cd ai_application
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

## Status

Sprint 1 in progress. The data pipeline is not built yet; run commands will
be added here as each step lands.
