# Direction model report - Sprint 1

Input: `data/clean/features_v1.parquet` (17,776 rows, EURUSD, GBPUSD, USDJPY).
Target: `next_day_up` (1 if the next close is higher). All numbers below are
printed by `python src/models/direction.py` or can be reproduced from
`reports/experiment_log.csv` and `reports/validation_table.csv`.

## Split

| Period     | Dates                           | Rows                  |
| ---------- | ------------------------------- | --------------------- |
| Train      | start of features to 2019-12-31 | [train rows]          |
| Validation | 2020-01-01 to 2022-12-31        | [validation rows]     |
| Test       | 2023-01-01 to end of data       | about 2,980, not used |

The split is by date and never shuffled. Train and validation together hold
14,794 rows, which is the number of rows in `predictions/predictions_v1.csv`.

## Models and baselines

| Model               | Type                                                  |
| ------------------- | ----------------------------------------------------- |
| always_up           | baseline, predicts UP every day                       |
| repeat_yesterday    | baseline, predicts today's direction again (per pair) |
| coin_flip           | baseline, random with a fixed seed                    |
| logistic_regression | standardised inputs, one model for all pairs          |
| random_forest       | 300 trees, max depth 5, at least 50 samples per leaf  |

Inputs are all numeric columns of `features_v1.parquet` ([number of features]
features, listed as `Features used` in the printout).

## Results on validation data

| Model               | Accuracy | Balanced accuracy | F1    |
| ------------------- | -------- | ----------------- | ----- |
| always_up           | 0.507    | 0.500             | 0.673 |
| repeat_yesterday    | 0.503    | 0.503             | 0.510 |
| coin_flip           | 0.505    | 0.505             | 0.509 |
| logistic_regression | 0.491    | 0.490             | 0.518 |
| random_forest       | 0.482    | 0.481             | 0.511 |

## What was checked

| Check                                     | Found                               | Action                      |
| ----------------------------------------- | ----------------------------------- | --------------------------- |
| Split overlaps in time                    | none (test in `test_direction.py`)  | none needed                 |
| Shuffling                                 | not used                            | none needed                 |
| Scaling fitted on future data             | no, scaler is fitted on train only  | none needed                 |
| Raw price columns as features             | excluded automatically              | none needed                 |
| Columns starting with `next_` as features | excluded automatically              | none needed                 |
| Yesterday baseline uses only past data    | yes, label shifted within each pair | none needed                 |
| Accuracy above 60% (leak warning)         | no model reached it                 | none needed                 |
| Test period                               | not scored or exported              | locked until the final test |

## Problems found and decisions

**No measurable edge.** Both models score about 50% and do not beat the
baselines. Validation accuracy of always_up is 0.507, so about 50.7% of
validation days are UP. The one to two point gaps between models and baselines
are within random noise for a validation set this size, so the correct
statement is "no edge shown", not "worse than a coin flip". No tuning was done
to improve the validation score.

**F1 of always_up is inflated.** It never predicts DOWN, so F1 (0.673) looks
good while balanced accuracy is exactly 0.500. Balanced accuracy is the main
comparison.

**Probabilities cluster around 0.5.** Over the 14,794 train and validation
rows, `prob_up` has mean 0.4998 and standard deviation 0.026. The middle half
lies between 0.487 and 0.514, the range is 0.32 to 0.74, and the extremes come
mostly from training rows, where the random forest is more confident. The
placeholder rule (BUY at 0.55 or above, SELL at 0.45 or below) will fire on
only a small share of days.

## Known limitations

- **One fixed train and validation split.** Scores are noisy. Walk-forward
  validation comes in Sprint 2.
- **One model for all pairs.** Pair-specific behaviour is not modelled.
- **No probability calibration.**
- **No regime information** is used yet.
- **Training-period predictions are in-sample.** `predictions_v1.csv` contains
  them, but only validation dates are suitable for a backtest.
- **Model choice uses the validation set.** The best model is picked by
  validation balanced accuracy, so the validation score is slightly optimistic.
