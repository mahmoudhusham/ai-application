"""Small helpers to read the shared files (the contract between teammates)."""
from pathlib import Path

import pandas as pd


def read_table(path):
    """Read .parquet or .csv into a DataFrame and parse the `date` column.

    If a .parquet file is requested but pyarrow is not installed (or the file
    does not exist), fall back to a .csv with the same name.
    """
    path = Path(path)
    csv_alt = path.with_suffix(".csv")
    if path.suffix == ".parquet":
        if path.exists():
            try:
                df = pd.read_parquet(path)
            except ImportError as exc:
                if not csv_alt.exists():
                    raise ImportError("Reading .parquet needs pyarrow: pip install pyarrow") from exc
                df = pd.read_csv(csv_alt)
        elif csv_alt.exists():
            df = pd.read_csv(csv_alt)
        else:
            raise FileNotFoundError(path)
    else:
        df = pd.read_csv(path)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
    return df
