"""Run the backtest end to end and write backtest_results.csv + an equity chart.

Usage:
    python -m src.backtest.run --prices data/processed/prices.parquet \
        --predictions data/processed/predictions_v1.csv \
        --regimes data/processed/regimes_v0.csv \
        --out-dir reports
"""
import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from src.backtest.backtester import run_backtest
from src.backtest.signal_rules import (
    buy_and_hold_signals,
    random_signals,
    signals_from_predictions,
)
from src.io_utils import read_table


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prices", default="data/processed/prices.parquet")
    ap.add_argument("--predictions", default="data/processed/predictions_v1.csv")
    ap.add_argument("--regimes", default=None)
    ap.add_argument("--buy", type=float, default=0.55)
    ap.add_argument("--sell", type=float, default=0.45)
    ap.add_argument("--slippage", type=float, default=0.0, help="extra pips per side")
    ap.add_argument("--cost-multiplier", type=float, default=1.0, help="2.0 = double the costs")
    ap.add_argument("--start", default=None, help="only backtest dates >= this (e.g. validation start)")
    ap.add_argument("--end", default=None, help="only backtest dates <= this")
    ap.add_argument("--out-dir", default="reports")
    args = ap.parse_args()

    prices = read_table(args.prices)
    pred = read_table(args.predictions)
    regimes = read_table(args.regimes) if args.regimes else None

    def clip(df):
        if args.start:
            df = df[df["date"] >= pd.Timestamp(args.start)]
        if args.end:
            df = df[df["date"] <= pd.Timestamp(args.end)]
        return df

    prices, pred = clip(prices), clip(pred)
    spread_map = None
    if args.cost_multiplier != 1.0:
        from src.backtest.backtester import DEFAULT_SPREAD_PIPS

        spread_map = {k: v * args.cost_multiplier for k, v in DEFAULT_SPREAD_PIPS.items()}

    # only backtest pairs and dates that the predictions cover, so strategies are comparable
    prices = prices[prices["pair"].isin(pred["pair"].unique())]
    strategies = {
        "direction_only": signals_from_predictions(pred, buy=args.buy, sell=args.sell),
        "buy_and_hold": buy_and_hold_signals(pred),
        "random_signals": random_signals(pred, seed=0),
    }
    if regimes is not None:
        strategies["direction_plus_regime"] = signals_from_predictions(
            pred, regimes, args.buy, args.sell, trending_only=True
        )

    rows, curves = [], {}
    for name, sig in strategies.items():
        r, d = run_backtest(prices, sig, name, spread_map, args.slippage)
        rows += r
        curves[name] = d
    res = pd.DataFrame(rows)

    out = Path(args.out_dir)
    (out / "figures").mkdir(parents=True, exist_ok=True)
    res.to_csv(out / "backtest_results.csv", index=False)

    pairs = sorted(curves["direction_only"])
    fig, axes = plt.subplots(len(pairs), 1, figsize=(11, 3.2 * len(pairs)), sharex=True)
    for ax, pair in zip(axes, pairs):
        for name, d in curves.items():
            ax.plot(d[pair].index, d[pair]["equity"], label=name, lw=1)
        ax.set_title(f"{pair}: equity after spread costs (start = 1.0)")
        ax.legend(fontsize=7, loc="upper left")
    fig.tight_layout()
    fig.savefig(out / "figures" / "equity_curves.png", dpi=120)
    print(res.round(4).to_string(index=False))
    print(f"\nSaved {out/'backtest_results.csv'} and {out/'figures'/'equity_curves.png'}")


if __name__ == "__main__":
    main()
