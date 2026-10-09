# 04 Image-blind baselines

Source: `analysis/04_feature_baseline.csv` (src/04_feature_baseline.py). Out-of-fold logits: `analysis/04_feature_baseline_oof_{clear,close}.csv`.

Features per post: title TF-IDF (word 1-2 grams, min_df 5, fit inside each fold), title length, [OC] flag, UTC posting hour one-hot (with a 'missing' level for date-only posts), weekday one-hot, year, chart type one-hot. Pair input = x_A - x_B. L2 logistic regression with no intercept, trained on both orientations; C picked by inner 5-fold CV on log loss. Outer 5-fold CV grouped by the month of post A. 95% CIs from 1,000 bootstrap resamples over pairs.

Year and chart type are identical within a pair (same ISO week, same type), so their differences are zero and they add nothing. The baseline's signal comes from the title, [OC], title length, hour and weekday.

| set | n | accuracy (95% CI) | AUC (95% CI) |
|---|---|---|---|
| clear | 2000 | 0.591 (0.570-0.611) | 0.623 (0.601-0.646) |
| close | 500 | 0.504 (0.460-0.550) | 0.534 (0.484-0.586) |

Title-only LLM baseline: not run yet. It needs the 'strongest API judge', which Step 5 calibration decides, and it spends API budget.
