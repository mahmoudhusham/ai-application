import pandas as pd

PAIRS = ["EURUSD", "GBPUSD", "USDJPY"]
PRICE_COLS = ["open", "high", "low", "close"]

# A close that jumps more than 3% and jumps back the next day is a data error.
SPIKE_LIMIT = 0.03
# A daily high-low range above 15% of the close never happened in these pairs.
RANGE_LIMIT = 0.15


def load_raw(pair):
    df = pd.read_csv(f"data/raw/{pair}.csv", header=[0, 1], index_col=0, parse_dates=True)
    df.columns = df.columns.droplevel(0)
    df = df.drop(columns="Volume")
    df.columns = df.columns.str.lower()
    df.index.name = "date"
    df = df.reset_index()
    df.insert(1, "pair", pair)
    return df


def drop_rows(df, bad, reason):
    print(f"{reason}: dropped {bad.sum()} rows")
    return df[~bad].reset_index(drop=True)


# 1. Load the three raw files and stack them into one long table.
df = pd.concat([load_raw(pair) for pair in PAIRS], ignore_index=True)
df = df.sort_values(["pair", "date"]).reset_index(drop=True)
print("raw rows:", len(df))

# 2. Basic problems: duplicates, missing prices, weekends, prices not above 0.
df = drop_rows(df, df.duplicated(subset=["date", "pair"]), "duplicate date")
df = drop_rows(df, df[PRICE_COLS].isna().any(axis=1), "missing price")
df = drop_rows(df, df["date"].dt.day_of_week >= 5, "weekend")
df = drop_rows(df, (df[PRICE_COLS] <= 0).any(axis=1), "price not positive")

# 3. Spikes: the close jumps one day and reverses the next.
ret = df.groupby("pair")["close"].pct_change()
next_ret = ret.groupby(df["pair"]).shift(-1)
spike = (ret.abs() > SPIKE_LIMIT) & (next_ret.abs() > SPIKE_LIMIT) & (ret * next_ret < 0)
df = drop_rows(df, spike, "close spike")

# 4. Impossible ranges: a high or low far away from the rest of the bar.
day_range = (df["high"] - df["low"]) / df["close"]
df = drop_rows(df, day_range > RANGE_LIMIT, "impossible range")

# 5. Small OHLC breaks: widen high and low so they contain open and close.
broken = (df["high"] < df[PRICE_COLS].max(axis=1)) | (df["low"] > df[PRICE_COLS].min(axis=1))
print(f"OHLC break: repaired {broken.sum()} rows")
df["high"] = df[PRICE_COLS].max(axis=1)
df["low"] = df[PRICE_COLS].min(axis=1)

# 6. Start all pairs on the first date where every pair has data.
start = df.groupby("pair")["date"].min().max()
df = drop_rows(df, df["date"] < start, f"before common start {start.date()}")

# 7. Save in the agreed format: date, pair, open, high, low, close.
df = df[["date", "pair"] + PRICE_COLS]
df.to_parquet("data/clean/prices.parquet", index=False)

print("clean rows:", len(df))
print(df.groupby("pair")["date"].agg(["min", "max", "count"]))
