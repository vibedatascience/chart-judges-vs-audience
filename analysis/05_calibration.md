# 05 Calibration on VisJudge-Bench

150 `single_view` items sampled with seed 20261008 (`pairs/calibration.parquet`). Prompt P2; judge score = mean of the six dimensions; target = `overall_score`. Images standardized the same way as beautiVis (white background, long side <= 1536, JPEG q90). 95% CI from 1,000 bootstrap resamples.

Published (VisJudge-Bench v3, 648-item test set, all three types): GPT-5 r=0.428 MAE=0.553; Claude-4-Sonnet r=0.465 MAE=0.622; Gemini-2.5-Pro r=0.265 MAE=0.662; Gemini-2.0-Flash r=0.395 MAE=0.682.

| judge            | model_id                                        |   n_ok |   n_fail |   pearson_r |   r_lo |   r_hi |   mae | published_model                   |   published_r |   published_mae |   abs_diff_r |   cost_usd |
|:-----------------|:------------------------------------------------|-------:|---------:|------------:|-------:|-------:|------:|:----------------------------------|--------------:|----------------:|-------------:|-----------:|
| gemini-2.5-flash | gemini-2.5-flash                                |    150 |        0 |       0.472 |  0.319 |  0.599 | 0.871 | Gemini-2.0-Flash / Gemini-2.5-Pro |       nan     |         nan     |      nan     |      0.107 |
| gpt-5            | gpt-5                                           |    150 |        0 |       0.414 |  0.262 |  0.537 | 0.622 | GPT-5                             |         0.428 |           0.553 |        0.014 |      0.231 |
| haiku-4.5        | global.anthropic.claude-haiku-4-5-20251001-v1:0 |    150 |        0 |       0.467 |  0.326 |  0.590 | 0.692 | Claude-4-Sonnet                   |       nan     |         nan     |      nan     |      0.258 |

Total spend after calibration: $0.87
