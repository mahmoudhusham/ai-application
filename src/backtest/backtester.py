"""Backtester: signals + prices in, daily P&L, equity curve and metrics out.

Conventions (agree these with the team):
- A signal on date D is known at the close of D. BUY=+1, SELL=-1, HOLD=0 (flat).
  The position earns the return from close D to close D+1 (never the same day).
- Fixed position size: 1 unit of notional per pair, returns are simple returns.
- Cost: the spread is paid on every change of position. Half the spread on each
  side, so a round trip (open + close) costs one full spread. A flip from long to
  short moves 2 units, so it costs one full spread. Slippage (optional) is extra
  pips per side. Any open position is closed (and paid for) on the last day.
- Costs are in pips: 1 pip = 0.0001, or 0.01 for JPY pairs.
"""
import numpy as np
import pandas as pd

POS = {"BUY": 1.0, "SELL": -1.0, "HOLD": 0.0}
# ASSUMPTION: typical retail spreads in pips. Confirm with the team / the broker you quote.
DEFAULT_SPREAD_PIPS = {"EURUSD": 1.0, "GBPUSD": 1.5, "USDJPY": 1.0}


def pip_size(pair):
    return 0.01 if pair.endswith("JPY") else 0.0001


def _extract_trades(pos, gross, half):
    """Split the position series into trades (runs of the same non-zero position)."""
    trades = []
    n = len(pos)
    i = 0
    while i < n:
        if pos[i] == 0:
            i += 1
            continue
        j = i
        while j + 1 < n and pos[j + 1] == pos[i]:
            j += 1
        exit_idx = j + 1 if j + 1 < n else j
        pnl_gross = gross[i : j + 1].sum()
        cost = half[i] + half[exit_idx]
        trades.append({"start": i, "end": j, "gross": pnl_gross, "net": pnl_gross - cost})
        i = j + 1
    return trades


def backtest_pair(prices, signals, pair, spread_pips=None, slippage_pips=0.0):
    """Backtest one pair. Returns (daily DataFrame, list of trades)."""
    if spread_pips is None:
        spread_pips = DEFAULT_SPREAD_PIPS.get(pair, 1.0)
    px = (
        prices[prices["pair"] == pair]
        .sort_values("date")
        .drop_duplicates("date")
        .set_index("date")["close"]
    )
    if len(px) < 3:
        raise ValueError(f"Not enough prices for {pair}")
    sig = (
        signals[signals["pair"] == pair]
        .drop_duplicates("date", keep="last")
        .set_index("date")["signal"]
    )
    unknown = set(sig.unique()) - set(POS)
    if unknown:
        raise ValueError(f"Unknown signal values: {unknown}")

    pos = sig.reindex(px.index).fillna("HOLD").map(POS).astype(float)
    ret_next = px.shift(-1) / px - 1  # return earned by the position held at D's close
    # the last day has no next-day return: drop it
    px, pos, ret_next = px.iloc[:-1], pos.iloc[:-1], ret_next.iloc[:-1]

    half = ((spread_pips / 2 + slippage_pips) * pip_size(pair)) / px  # cost per unit traded
    turnover = (pos - pos.shift(1).fillna(0.0)).abs()
    cost = turnover * half
    cost.iloc[-1] += abs(pos.iloc[-1]) * half.iloc[-1]  # close open position at the end

    gross = pos * ret_next
    net = gross - cost
    daily = pd.DataFrame(
        {"pos": pos, "gross": gross, "cost": cost, "net": net, "equity": (1 + net).cumprod()}
    )
    trades = _extract_trades(pos.values, gross.values, half.values)
    return daily, trades


def _metrics(net, trades):
    equity = (1 + net).cumprod()
    std = net.std()
    sharpe = float(net.mean() / std * np.sqrt(252)) if std and std > 0 else float("nan")
    drawdown = float((equity / equity.cummax() - 1).min())
    wins = [t["net"] > 0 for t in trades]
    return {
        "total_return": float(equity.iloc[-1] - 1),
        "sharpe": sharpe,
        "max_drawdown": drawdown,
        "win_rate": float(np.mean(wins)) if wins else float("nan"),
        "n_trades": len(trades),
    }


def run_backtest(prices, signals, strategy, spread_map=None, slippage_pips=0.0):
    """Backtest every pair in `signals`, plus an equal-weight 'ALL' portfolio.

    Returns (results rows as list of dicts, dict of daily frames keyed by pair).
    """
    spread_map = {**DEFAULT_SPREAD_PIPS, **(spread_map or {})}
    rows, dailies, all_trades = [], {}, []
    for pair in sorted(signals["pair"].unique()):
        daily, trades = backtest_pair(prices, signals, pair, spread_map.get(pair), slippage_pips)
        dailies[pair] = daily
        all_trades += trades
        rows.append({"pair": pair, "strategy": strategy, **_metrics(daily["net"], trades)})
    port = pd.concat([d["net"].rename(p) for p, d in dailies.items()], axis=1).mean(axis=1)
    dailies["ALL"] = pd.DataFrame({"net": port, "equity": (1 + port).cumprod()})
    rows.append({"pair": "ALL", "strategy": strategy, **_metrics(port, all_trades)})
    return rows, dailies
