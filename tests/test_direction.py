"""Tests for the direction model.

Run from the repo's main folder:
    python -m pytest tests/test_direction.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "models"))
import direction as d  # noqa: E402


def make_df():
    dates = pd.bdate_range("2019-12-20", "2020-01-20")
    rows = []
    for pair in ["EURUSD", "GBPUSD"]:
        for i, dt in enumerate(dates):
            rows.append({"date": dt, "pair": pair, "f1": float(i),
                         "next_day_up": i % 2})
    return pd.DataFrame(rows).sort_values(["pair", "date"]).reset_index(drop=True)


def test_split_is_in_time_order_and_has_no_overlap():
    train, val, test = d.time_split(make_df(), "2019-12-31", "2020-01-10")
    assert train.date.max() <= pd.Timestamp("2019-12-31")
    assert val.date.min() > pd.Timestamp("2019-12-31")
    assert val.date.max() <= pd.Timestamp("2020-01-10")
    assert test.date.min() > pd.Timestamp("2020-01-10")
    assert len(train) + len(val) + len(test) == len(make_df())


def test_yesterday_direction_is_per_pair_and_uses_only_the_past():
    df = make_df()
    y = d.yesterday_direction(df)
    for pair in ["EURUSD", "GBPUSD"]:
        sub = df[df.pair == pair]
        ys = y[sub.index]
        assert np.isnan(ys.iloc[0])                       # first day has no yesterday
        assert (ys.iloc[1:].values == sub.next_day_up.iloc[:-1].values).all()


def test_pick_features_drops_prices_and_future_columns():
    df = make_df()
    df["close"] = 1.1
    df["next_day_return"] = 0.01
    feats, dropped = d.pick_features(df)
    assert feats == ["f1"]
    assert {c for c, _ in dropped} == {"close", "next_day_return"}
