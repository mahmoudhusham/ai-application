import pandas as pd
import pytest

from features import FEATURE_COLS, build_features, features_for_one_pair


@pytest.fixture(scope="module")
def prices():
    return pd.read_parquet("data/clean/prices.parquet")


@pytest.fixture(scope="module")
def features(prices):
    return build_features(prices)


def test_columns_match_the_contract(features):
    assert list(features.columns) == ["date", "pair"] + FEATURE_COLS + ["next_day_up"]


def test_no_missing_values_and_label_is_0_or_1(features):
    assert features.isna().sum().sum() == 0
    assert set(features["next_day_up"]) == {0, 1}


def test_label_is_the_next_close_of_the_same_pair(prices, features):
    for pair, one_pair in prices.groupby("pair"):
        one_pair = one_pair.sort_values("date").reset_index(drop=True)
        closes = dict(zip(one_pair["date"], one_pair["close"]))
        next_date = dict(zip(one_pair["date"][:-1], one_pair["date"][1:]))
        for row in features[features["pair"] == pair].itertuples():
            expected = int(closes[next_date[row.date]] > closes[row.date])
            assert row.next_day_up == expected, f"{pair} {row.date}"


def test_features_do_not_change_when_the_future_is_removed(prices):
    # Compute features twice: from all prices, and from prices that stop at the
    # cutoff. A feature that only looks backwards gives the same values on the
    # shared dates. A feature that used future data would differ near the cutoff.
    cutoff = pd.Timestamp("2015-06-30")
    for pair, one_pair in prices.groupby("pair"):
        one_pair = one_pair.sort_values("date")
        full = features_for_one_pair(one_pair)
        cut = features_for_one_pair(one_pair[one_pair["date"] <= cutoff])
        assert len(cut) > 1000
        pd.testing.assert_frame_equal(cut, full.iloc[: len(cut)])
