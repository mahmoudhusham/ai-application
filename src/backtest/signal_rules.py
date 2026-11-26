"""Baseline strategies and the simple prob_up -> BUY/SELL/HOLD rule.

The final signal generator is Mahmoud's (Sprint 3). This is the minimum Kur needs
to backtest predictions_v1.csv in Sprint 1 and to run the Sprint 2 threshold analysis.
"""
import numpy as np
import pandas as pd


def buy_and_hold_signals(prices):
    out = prices[["date", "pair"]].copy()
    out["signal"] = "BUY"
    return out


def random_signals(prices, seed=0):
    rng = np.random.default_rng(seed)
    out = prices[["date", "pair"]].copy()
    out["signal"] = rng.choice(["BUY", "SELL", "HOLD"], size=len(out))
    return out


def signals_from_predictions(pred, regimes=None, buy=0.55, sell=0.45, trending_only=False):
    """BUY if prob_up >= buy, SELL if prob_up <= sell, else HOLD.

    If trending_only, anything not in a TRENDING regime becomes HOLD
    (a missing regime also counts as HOLD).
    """
    df = pred[["date", "pair", "prob_up"]].copy()
    df["signal"] = np.where(df["prob_up"] >= buy, "BUY", np.where(df["prob_up"] <= sell, "SELL", "HOLD"))
    if trending_only:
        if regimes is None:
            raise ValueError("trending_only needs regimes")
        df = df.merge(regimes[["date", "pair", "regime"]], on=["date", "pair"], how="left")
        df.loc[df["regime"] != "TRENDING", "signal"] = "HOLD"
    return df[["date", "pair", "signal", "prob_up"]]
