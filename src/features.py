import pandas as pd

FEATURE_COLS = [
    "ret_1d", "ret_lag1", "ret_lag2", "ret_lag3", "ret_lag5",
    "ma_5_ratio", "ma_20_ratio", "rsi_14", "atr_14_pct", "vol_20",
]


def features_for_one_pair(df):
    """df holds one pair, sorted by date. Every feature only looks backwards."""
    out = df[["date", "pair"]].copy()
    close = df["close"]
    prev_close = close.shift(1)

    # Returns: today's close against yesterday's, then the same value from earlier days.
    out["ret_1d"] = close / prev_close - 1
    for lag in [1, 2, 3, 5]:
        out[f"ret_lag{lag}"] = out["ret_1d"].shift(lag)

    # Moving averages, as "how far is the close above its average".
    out["ma_5_ratio"] = close / close.rolling(5).mean() - 1
    out["ma_20_ratio"] = close / close.rolling(20).mean() - 1

    # RSI 14: average gain against average loss, on a 0-100 scale.
    change = close.diff()
    avg_gain = change.clip(lower=0).ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    avg_loss = (-change).clip(lower=0).ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    out["rsi_14"] = 100 - 100 / (1 + avg_gain / avg_loss)

    # ATR 14: average size of the daily range, as a fraction of the close.
    true_range = pd.concat(
        [df["high"] - df["low"], (df["high"] - prev_close).abs(), (df["low"] - prev_close).abs()],
        axis=1,
    ).max(axis=1)
    atr = true_range.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    out["atr_14_pct"] = atr / close

    # Rolling volatility: how much the daily return varied over the last 20 days.
    out["vol_20"] = out["ret_1d"].rolling(20).std()

    return out


def label_for_one_pair(df):
    """1 if the NEXT row's close is higher. The only code that looks forward."""
    next_close = df["close"].shift(-1)
    label = (next_close > df["close"]).astype(float)
    label[next_close.isna()] = float("nan")  # the last day has no next day
    return label


def build_features(prices):
    prices = prices.sort_values(["pair", "date"])
    parts = []
    for _, one_pair in prices.groupby("pair"):
        out = features_for_one_pair(one_pair)
        out["next_day_up"] = label_for_one_pair(one_pair)
        out = out.dropna(subset=["next_day_up"])
        out["next_day_up"] = out["next_day_up"].astype(int)
        parts.append(out)
    features = pd.concat(parts, ignore_index=True)
    # The first rows of each pair have no history yet for the 20-day windows.
    return features.dropna(subset=FEATURE_COLS).reset_index(drop=True)


if __name__ == "__main__":
    prices = pd.read_parquet("data/clean/prices.parquet")
    features = build_features(prices)
    features.to_parquet("data/clean/features_v1.parquet", index=False)

    print("rows:", len(features))
    print(features.groupby("pair")["date"].agg(["min", "max", "count"]))
    print("share of up days:")
    print(features.groupby("pair")["next_day_up"].mean().round(3))
