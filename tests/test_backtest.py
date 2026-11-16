import numpy as np
import pandas as pd
import pytest

from src.backtest.backtester import backtest_pair, run_backtest
from src.backtest.signal_rules import buy_and_hold_signals, random_signals


def make_prices(closes, pair="EURUSD"):
    dates = pd.bdate_range("2020-01-01", periods=len(closes))
    return pd.DataFrame({"date": dates, "pair": pair, "close": closes})


def sigs(prices, values):
    return pd.DataFrame({"date": prices["date"], "pair": prices["pair"], "signal": values})


def test_signal_earns_next_day_return_not_same_day():
    p = make_prices([100.0, 110.0, 121.0, 121.0])
    s = sigs(p, ["BUY", "BUY", "HOLD", "HOLD"])
    daily, _ = backtest_pair(p, s, "EURUSD", spread_pips=0.0)
    # BUY at D0 earns D0->D1 (+10%), BUY at D1 earns D1->D2 (+10%)
    assert daily["gross"].iloc[0] == pytest.approx(0.10)
    assert daily["gross"].iloc[1] == pytest.approx(0.10)
    assert daily["equity"].iloc[-1] == pytest.approx(1.21)


def test_round_trip_costs_one_full_spread():
    p = make_prices([1.0] * 6)  # flat price, so P&L is only the cost
    s = sigs(p, ["BUY", "BUY", "HOLD", "HOLD", "HOLD", "HOLD"])
    daily, trades = backtest_pair(p, s, "EURUSD", spread_pips=2.0)
    assert len(trades) == 1
    assert daily["equity"].iloc[-1] - 1 == pytest.approx(-0.0002, abs=1e-7)  # 2 pips of 1.0
    assert trades[0]["net"] < 0


def test_flip_long_to_short_costs_one_full_spread():
    p = make_prices([1.0] * 6)
    s = sigs(p, ["BUY", "BUY", "SELL", "SELL", "HOLD", "HOLD"])
    daily, trades = backtest_pair(p, s, "EURUSD", spread_pips=2.0)
    # open long (half) + flip (full) + close short (half) = 2 full spreads
    assert daily["cost"].sum() == pytest.approx(0.0004, abs=1e-9)
    assert len(trades) == 2


def test_open_position_is_closed_and_paid_on_last_day():
    p = make_prices([1.0] * 5)
    s = sigs(p, ["BUY"] * 5)
    daily, trades = backtest_pair(p, s, "EURUSD", spread_pips=2.0)
    assert daily["cost"].sum() == pytest.approx(0.0002, abs=1e-9)
    assert len(trades) == 1


def test_jpy_pip_size():
    p = make_prices([100.0] * 5, pair="USDJPY")
    s = sigs(p, ["BUY", "HOLD", "HOLD", "HOLD", "HOLD"])
    daily, _ = backtest_pair(p, s, "USDJPY", spread_pips=1.0)
    assert daily["cost"].sum() == pytest.approx(0.01 / 100.0, abs=1e-9)  # 1 pip = 0.01 on 100


def test_unknown_signal_value_raises():
    p = make_prices([1.0] * 5)
    with pytest.raises(ValueError):
        backtest_pair(p, sigs(p, ["BUY", "LONG", "HOLD", "HOLD", "HOLD"]), "EURUSD")


def _random_walk_prices(n=3000, seed=1):
    rng = np.random.default_rng(seed)
    close = 1.2 * np.exp(np.cumsum(rng.normal(0, 0.005, n)))
    return make_prices(close)


def test_buy_and_hold_pays_only_entry_and_exit():
    p = _random_walk_prices()
    daily, trades = backtest_pair(p, buy_and_hold_signals(p), "EURUSD", spread_pips=1.0)
    assert len(trades) == 1
    assert daily["cost"].sum() < 0.001  # two half-spreads, about 1 pip of 1.2


def test_random_signals_lose_roughly_the_costs():
    p = _random_walk_prices()
    gross_totals, cost_totals = [], []
    for seed in range(30):
        daily, _ = backtest_pair(p, random_signals(p, seed), "EURUSD", spread_pips=1.0)
        gross_totals.append(daily["gross"].sum())
        cost_totals.append(daily["cost"].sum())
    # random signals have no edge: gross is about 0 on average, so net is about minus the costs
    assert abs(np.mean(gross_totals)) < 0.15 * np.std(gross_totals) * 3 + 0.05
    assert np.mean(cost_totals) > 0
    assert np.mean(gross_totals) - np.mean(cost_totals) < np.mean(gross_totals)


def test_run_backtest_returns_all_columns_and_all_row():
    p = pd.concat([_random_walk_prices(500, 1), _random_walk_prices(500, 2).assign(pair="GBPUSD")])
    rows, dailies = run_backtest(p, buy_and_hold_signals(p), "buy_and_hold")
    df = pd.DataFrame(rows)
    assert list(df.columns) == ["pair", "strategy", "total_return", "sharpe", "max_drawdown", "win_rate", "n_trades"]
    assert set(df["pair"]) == {"EURUSD", "GBPUSD", "ALL"}
    assert "ALL" in dailies
