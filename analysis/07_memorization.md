# 07 Memorization

## Training cutoffs

- gpt-5: 2024-09-30 (https://developers.openai.com/api/docs/models/gpt-5)
- haiku-4.5: 2025-02-28 (https://platform.claude.com/docs/en/models/haiku-4-5/overview (reliable Feb 2025; training data Jul 2025))
- gemini-2.5-flash: 2025-01-31 (https://ai.google.dev/gemini-api/docs/models/gemini-2.5-flash)

## Accuracy by cutoff group (clear pairs)

| judge            | prompt   | cutoff     | cutoff_source                                                                                             | group   |   n_pairs |   accuracy |    lo |    hi |
|:-----------------|:---------|:-----------|:----------------------------------------------------------------------------------------------------------|:--------|----------:|-----------:|------:|------:|
| gpt-5            | P1       | 2024-09-30 | https://developers.openai.com/api/docs/models/gpt-5                                                       | post    |        37 |      0.581 | 0.446 | 0.703 |
| gpt-5            | P1       | 2024-09-30 | https://developers.openai.com/api/docs/models/gpt-5                                                       | pre     |       463 |      0.579 | 0.537 | 0.619 |
| gpt-5            | P3       | 2024-09-30 | https://developers.openai.com/api/docs/models/gpt-5                                                       | post    |        17 |      0.706 | 0.500 | 0.882 |
| gpt-5            | P3       | 2024-09-30 | https://developers.openai.com/api/docs/models/gpt-5                                                       | pre     |       233 |      0.631 | 0.569 | 0.687 |
| haiku-4.5        | P1       | 2025-02-28 | https://platform.claude.com/docs/en/models/haiku-4-5/overview (reliable Feb 2025; training data Jul 2025) | pre     |       500 |      0.555 | 0.520 | 0.590 |
| haiku-4.5        | P3       | 2025-02-28 | https://platform.claude.com/docs/en/models/haiku-4-5/overview (reliable Feb 2025; training data Jul 2025) | pre     |       250 |      0.564 | 0.512 | 0.620 |
| gemini-2.5-flash | P1       | 2025-01-31 | https://ai.google.dev/gemini-api/docs/models/gemini-2.5-flash                                             | pre     |       500 |      0.587 | 0.555 | 0.618 |
| gemini-2.5-flash | P3       | 2025-01-31 | https://ai.google.dev/gemini-api/docs/models/gemini-2.5-flash                                             | pre     |       500 |      0.564 | 0.535 | 0.593 |

## Recognition probe: top 50 posts by score (the brief says 200; reduced for the $10 cap)

| judge            |   n |   claimed_seen |   recall_rate |   parse_rate | flag_contaminated   |
|:-----------------|----:|---------------:|--------------:|-------------:|:--------------------|
| gemini-2.5-flash |  50 |          0.620 |         0.200 |        1.000 | True                |
| gpt-5            |  50 |          0.060 |         0.020 |        1.000 | False               |
| haiku-4.5        |  50 |          0.200 |         0.100 |        1.000 | True                |

Recall = seen and token_set_ratio(guessed title, true title) >= 80. Flag if recall rate > 5%.

Total spend: $8.77
