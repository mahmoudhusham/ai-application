import numpy as np
import pandas as pd

from src.regime.rule_based import adx, label_regimes


def make_ohlc(close, pair="EURUSD"):
    close = np.asarray(close, dtype=float)
    return pd.DataFrame(
        {
            "date": pd.bdate_range("2020-01-01", periods=len(close)),
            "pair": pair,
            "open": close,
            "high": close * 1.002,
            "low": close * 0.998,
            "close": close,
        }
    )


def test_steady_trend_is_trending():
    n = np.arange(300)
    reg = label_regimes(make_ohlc(100 * 1.002**n))
    assert (reg["regime"].iloc[-100:] == "TRENDING").all()


def test_sideways_oscillation_is_ranging():
    n = np.arange(300)
    reg = label_regimes(make_ohlc(100 + 2 * np.sin(2 * np.pi * n / 10)))
    assert (reg["regime"].iloc[-100:] == "RANGING").all()


def test_no_lookahead_labels_do_not_change_when_future_is_removed():
    rng = np.random.default_rng(0)
    close = 100 * np.exp(np.cumsum(rng.normal(0, 0.005, 400)))
    full = label_regimes(make_ohlc(close))
    cut = label_regimes(make_ohlc(close[:250]))
    merged = cut.merge(full, on=["date", "pair"], suffixes=("_cut", "_full"))
    assert len(merged) == len(cut)
    assert (merged["regime_cut"] == merged["regime_full"]).all()
    assert np.allclose(merged["trend_strength_cut"], merged["trend_strength_full"])


def test_warmup_rows_are_dropped_and_adx_in_range():
    df = make_ohlc(100 + np.random.default_rng(1).normal(0, 1, 200).cumsum())
    a = adx(df)
    assert a.iloc[:13].isna().all()
    assert a.dropna().between(0, 100).all()
