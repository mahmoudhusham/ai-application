"""Draw the regime over the price chart for one pair (Sprint 1 checkpoint).

Usage:
    python -m src.regime.plot_regime --pair EURUSD --last-years 3
"""
import argparse

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.io_utils import read_table


def plot_regime(prices, regimes, pair, out, last_years=None, threshold=25.0):
    p = prices[prices["pair"] == pair].sort_values("date")
    r = regimes[regimes["pair"] == pair].sort_values("date")
    d = p.merge(r[["date", "regime", "trend_strength"]], on="date", how="inner")
    if last_years:
        d = d[d["date"] >= d["date"].max() - __import__("pandas").DateOffset(years=last_years)]
    d = d.reset_index(drop=True)

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(12, 7), sharex=True, gridspec_kw={"height_ratios": [3, 1]}
    )
    ax1.plot(d["date"], d["close"], color="black", lw=1)
    # shade TRENDING stretches
    trending = (d["regime"] == "TRENDING").values
    start = None
    for i, t in enumerate(trending):
        if t and start is None:
            start = i
        if (not t or i == len(trending) - 1) and start is not None:
            end = i if not t else i
            ax1.axvspan(d["date"][start], d["date"][end], color="tab:green", alpha=0.2, lw=0)
            start = None
    ax1.set_title(f"{pair}: close price, green = TRENDING, white = RANGING")
    ax1.set_ylabel("close")
    ax2.plot(d["date"], d["trend_strength"], color="tab:blue", lw=1)
    ax2.axhline(threshold, color="red", ls="--", lw=1, label=f"ADX = {threshold:g}")
    ax2.set_ylabel("ADX")
    ax2.legend(loc="upper left")
    fig.tight_layout()
    fig.savefig(out, dpi=130)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prices", default="data/processed/prices.parquet")
    ap.add_argument("--regimes", default="data/processed/regimes_v0.csv")
    ap.add_argument("--pair", default="EURUSD")
    ap.add_argument("--last-years", type=int, default=3)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    out = args.out or f"reports/figures/regime_{args.pair}.png"
    plot_regime(read_table(args.prices), read_table(args.regimes), args.pair, out, args.last_years)
    print("Saved", out)


if __name__ == "__main__":
    main()
