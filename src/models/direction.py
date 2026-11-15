"""Next-day direction model.

Splits the data by time, scores naive baselines, trains logistic regression
and a random forest, logs each run and exports the predicted probabilities.

Run from the repo folder:
    python src/models/direction.py
"""
import argparse
import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

# Repo root (src/models/ -> src/ -> repo/), so paths work from any folder
ROOT = Path(__file__).resolve().parents[2]

FEATURES_PATH = ROOT / "data" / "clean" / "features_v1.parquet"
LOG_PATH = ROOT / "reports" / "experiment_log.csv"
TABLE_PATH = ROOT / "reports" / "validation_table.csv"
PRED_PATH = ROOT / "predictions" / "predictions_v1.csv"

# Split dates: train up to TRAIN_END, validation up to VAL_END, test after that
TRAIN_END = "2019-12-31"
VAL_END = "2022-12-31"

LABEL = "next_day_up"
NON_FEATURE_COLS = ["date", "pair", LABEL]
RAW_PRICE_COLS = {"open", "high", "low", "close", "adj close", "adj_close", "volume"}
MODEL_VERSION = "v1.0"
SEED = 42


# ---------------------------------------------------------------- data
def load_features(path: Path) -> pd.DataFrame:
    """Read the features file and check the required columns exist."""
    if not Path(path).exists():
        raise SystemExit(f"Cannot find {path}")
    df = pd.read_parquet(path)
    if "date" not in [str(c).lower() for c in df.columns] and (
            df.index.name and str(df.index.name).lower() == "date"):
        df = df.reset_index()
    df.columns = [str(c).strip().lower() for c in df.columns]

    missing = [c for c in ["date", "pair", LABEL] if c not in df.columns]
    if missing:
        raise SystemExit(f"Missing columns {missing}. "
                         f"Found: {df.columns.tolist()}")
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values(["pair", "date"]).reset_index(drop=True)


def pick_features(df: pd.DataFrame):
    """Return (usable feature columns, [(skipped column, reason), ...])."""
    feats, dropped = [], []
    for c in df.columns:
        if c in NON_FEATURE_COLS or c == "_yesterday":
            continue
        if c in RAW_PRICE_COLS:
            dropped.append((c, "raw price level"))
        elif c.startswith("next_"):
            dropped.append((c, "future value, leak risk"))
        elif not pd.api.types.is_numeric_dtype(df[c]):
            dropped.append((c, "not numeric"))
        else:
            feats.append(c)
    return feats, dropped


# ---------------------------------------------------------- evaluation
def time_split(df: pd.DataFrame, train_end: str, val_end: str):
    """Split by date, never shuffled. Returns train, validation, test."""
    d = pd.to_datetime(df["date"])
    train = df[d <= train_end]
    val = df[(d > train_end) & (d <= val_end)]
    test = df[d > val_end]
    return train, val, test


def metrics(y_true, y_pred) -> dict:
    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "balanced_acc": balanced_accuracy_score(y_true, y_pred),
        "f1": f1_score(y_true, y_pred, zero_division=0),
    }


# ----------------------------------------------------------- baselines
def yesterday_direction(df: pd.DataFrame) -> pd.Series:
    """Direction of today's move = previous row's label, within each pair.
    Expects df sorted by pair, date."""
    return df.groupby("pair")[LABEL].shift(1)


def baseline_predictions(n: int, yesterday: pd.Series, rng) -> dict:
    return {
        "always_up": np.ones(n, dtype=int),
        "repeat_yesterday": yesterday.fillna(1).astype(int).to_numpy(),
        "coin_flip": rng.integers(0, 2, n),
    }


# -------------------------------------------------------------- models
def build_models() -> dict:
    return {
        # scaler sits inside the pipeline so it is fitted on training data only
        "logistic_regression": make_pipeline(
            StandardScaler(), LogisticRegression(C=1.0, max_iter=1000)),
        # shallow trees and large leaves to limit overfitting
        "random_forest": RandomForestClassifier(
            n_estimators=300, max_depth=5, min_samples_leaf=50,
            n_jobs=-1, random_state=SEED),
    }


# ------------------------------------------------------ experiment log
def log_experiment(row: dict):
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    new = pd.DataFrame([row])
    if LOG_PATH.exists():
        new = pd.concat([pd.read_csv(LOG_PATH), new], ignore_index=True)
    new.to_csv(LOG_PATH, index=False)


# ---------------------------------------------------------------- main
def main(features_path: Path, train_end: str, val_end: str):
    rng = np.random.default_rng(SEED)
    df = load_features(features_path)
    df["_yesterday"] = yesterday_direction(df)

    feature_cols, dropped = pick_features(df)
    for name, why in dropped:
        print(f"Skipping column '{name}' ({why})")
    if not feature_cols:
        raise SystemExit("No usable feature columns found.")

    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.dropna(subset=feature_cols + [LABEL]).reset_index(drop=True)
    df[LABEL] = df[LABEL].astype(int)

    train, val, test = time_split(df, train_end, val_end)
    if len(train) == 0 or len(val) == 0:
        raise SystemExit(
            f"Train has {len(train)} rows, validation has {len(val)} rows. "
            f"Data runs {df.date.min().date()} to {df.date.max().date()}; "
            "adjust TRAIN_END / VAL_END.")

    print(f"Features file : {features_path}")
    print(f"Pairs         : {sorted(df['pair'].unique())}")
    print(f"Features used : {feature_cols}")
    print(f"Train {train.date.min().date()}..{train.date.max().date()} ({len(train)} rows)")
    print(f"Val   {val.date.min().date()}..{val.date.max().date()} ({len(val)} rows)")
    print(f"Test  {len(test)} rows (not used)")
    print(f"Share of UP days in train: {train[LABEL].mean():.3f}\n")

    X_tr, y_tr = train[feature_cols], train[LABEL]
    X_va, y_va = val[feature_cols], val[LABEL]
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    split_txt = f"train<={train_end}, val<={val_end}"
    results = []

    # baselines, scored on validation
    for name, pred in baseline_predictions(len(y_va), val["_yesterday"], rng).items():
        m = metrics(y_va, pred)
        results.append({"model": name, **m})
        log_experiment({"time": stamp, "model": name, "features": "none",
                        "settings": "-", "split": split_txt,
                        **{f"val_{k}": round(v, 4) for k, v in m.items()}})

    # models
    fitted = {}
    for name, model in build_models().items():
        model.fit(X_tr, y_tr)
        prob = model.predict_proba(X_va)[:, 1]
        m = metrics(y_va, (prob >= 0.5).astype(int))
        results.append({"model": name, **m})
        fitted[name] = model
        log_experiment({"time": stamp, "model": name,
                        "features": json.dumps(feature_cols),
                        "settings": str(model.get_params(deep=False))[:300],
                        "split": split_txt,
                        **{f"val_{k}": round(v, 4) for k, v in m.items()}})

    table = pd.DataFrame(results).set_index("model").round(4)
    print("Validation results:")
    print(table.to_string(), "\n")

    if (table.loc[list(fitted), "accuracy"] > 0.60).any():
        print("WARNING: accuracy above 60% on FX direction is suspicious; "
              "check for look-ahead leakage.\n")

    best = table.loc[list(fitted), "balanced_acc"].idxmax()
    print(f"Best model (validation balanced accuracy): {best}")

    # export probabilities for train and validation rows (test rows excluded)
    keep = pd.concat([train, val])
    out = keep[["date", "pair"]].copy()
    out["prob_up"] = fitted[best].predict_proba(keep[feature_cols])[:, 1].round(4)
    out["model_version"] = MODEL_VERSION
    out["date"] = out["date"].dt.strftime("%Y-%m-%d")
    PRED_PATH.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(PRED_PATH, index=False)
    print(f"Wrote {PRED_PATH} ({len(out)} rows)\n")

    # random forest feature importance
    imp = pd.Series(fitted["random_forest"].feature_importances_,
                    index=feature_cols).sort_values(ascending=False)
    print("Random forest feature importance:")
    print(imp.round(3).to_string())
    TABLE_PATH.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(TABLE_PATH)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--features", default=str(FEATURES_PATH))
    ap.add_argument("--train-end", default=TRAIN_END)
    ap.add_argument("--val-end", default=VAL_END)
    a = ap.parse_args()
    main(Path(a.features), a.train_end, a.val_end)
