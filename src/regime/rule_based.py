"""Regime labeller v0 (rule-based): TRENDING vs RANGING from ADX.

A row dated D only uses prices up to the close of day D (no look-ahead).

Usage:
    python -m src.regime.rule_based --prices data/clean/prices.parquet \
        --out data/clean/regimes_v0.csv
"""
import argparse

import numpy as np
import pandas as pd

from src.io_utils import read_table


def adx(df, n=14):
    """Average Directional Index (Wilder smoothing). Needs high, low, close."""
    high, low, close = df["high"], df["low"], df["close"]
    up = high.diff()
    down = -low.diff()
    plus_dm = pd.Series(np.where((up > down) & (up > 0), up, 0.0), index=df.index)
    minus_dm = pd.Series(np.where((down > up) & (down > 0), down, 0.0), index=df.index)
    prev_close = close.shift(1)
    tr = pd.concat(
        [high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1
    ).max(axis=1)

    kw = dict(alpha=1.0 / n, adjust=False, min_periods=n)
    atr = tr.ewm(**kw).mean()
    plus_di = 100 * plus_dm.ewm(**kw).mean() / atr
    minus_di = 100 * minus_dm.ewm(**kw).mean() / atr
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
    return dx.ewm(**kw).mean()


def label_regimes(prices, adx_window=14, threshold=25.0):
    """Return DataFrame: date, pair, regime (TRENDING/RANGING), trend_strength (=ADX)."""
    out = []
    for pair, g in prices.sort_values(["pair", "date"]).groupby("pair"):
        g = g.reset_index(drop=True)
        a = adx(g, adx_window)
        r = pd.DataFrame(
            {
                "date": g["date"],
                "pair": pair,
                "regime": np.where(a >= threshold, "TRENDING", "RANGING"),
                "trend_strength": a.round(4),
            }
        )
        out.append(r[a.notna().values])  # drop warm-up rows with no ADX yet
    return pd.concat(out, ignore_index=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prices", default="data/clean/prices.parquet")
    ap.add_argument("--out", default="data/clean/regimes_v0.csv")
    ap.add_argument("--window", type=int, default=14)
    ap.add_argument("--threshold", type=float, default=25.0)
    args = ap.parse_args()

    prices = read_table(args.prices)
    reg = label_regimes(prices, args.window, args.threshold)
    reg.to_csv(args.out, index=False)
    share = reg.groupby("pair")["regime"].value_counts(normalize=True).round(3)
    print(f"Wrote {len(reg)} rows to {args.out}")
    print(share)


if __name__ == "__main__":
    main()
