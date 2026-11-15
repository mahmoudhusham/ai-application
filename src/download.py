from datetime import datetime
import yfinance as yf

start_date = datetime(year=2000, month=1, day=1)
end_date = datetime(year=2026, month=11, day=1)

tickers = ["EURUSD=X" , "GBPUSD=X" , "USDJPY=X"]


for ticker in tickers:
    name = ticker.split("=")[0]
    df_single = yf.download(
        tickers=ticker,
        start=start_date,
        end=end_date,
        interval="1d",
        auto_adjust=True,
        progress=False
    )
    df_single.to_csv(f"data/raw/{name}.csv")

