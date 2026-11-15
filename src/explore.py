import pandas as pd


df = pd.read_csv("data/raw/EURUSD.csv", header= [0, 1], index_col = 0, parse_dates = True)
df.columns = df.columns.droplevel(0)


print(df.index.duplicated().sum())
print(df.isna().sum())
print(df.index.day_of_week.value_counts().sort_index())

gaps = df.index.to_series().diff()
print(gaps.value_counts().sort_index())
print(gaps.sort_values(ascending=False).head(5))

prices = df[["Open", "High", "Low", "Close"]]
not_positive = (prices <= 0).any(axis=1)
low_above_open = df["Low"] > df["Open"]
low_above_close = df["Low"] > df["Close"]
close_above_high = df["Close"] > df["High"]
open_above_high = df["Open"] > df["High"]

print("not positive:", not_positive.sum())
print("low > open:", low_above_open.sum())
print("low > close:", low_above_close.sum())
print("close > high:", close_above_high.sum())
print("open > high:", open_above_high.sum())

bad = not_positive | low_above_open | low_above_close | close_above_high | open_above_high
print("rows breaking any rule:", bad.sum(), "of", len(df))
