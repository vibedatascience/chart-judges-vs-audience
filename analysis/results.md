# Results: do LLM chart judges agree with what audiences reward?

Status 2026-10-09. Every number below comes from a CSV in `analysis/`, named in brackets. To reproduce, run `src/` in step order with `PYTHONPATH=lib:src`. Judge outputs are cached in `judges/cache/`, so reruns cost nothing.

**Scope (because of the $10 cap; see LOG.md):**
- Judges: gpt-5 (minimal reasoning), Claude Haiku 4.5 and Gemini 2.5 Flash.
- Test set: the first 500 of the 2,000 clear pairs (balanced by year).
- P3 ran on 250 pairs for gpt-5 and Haiku and on 500 for Flash. P2 ran on 150 pairs, gpt-5 only. Close pairs: 200, Flash P1 only.
- Pair scoring: 1 = right, 0 = wrong, 0.5 = tie (P1/P2), or the two orders disagree (P3), or a call failed.
- There were 0 parse or API failures in all 7,150 judge tasks (including calibration and title-only).

## RQ1: can judges pick the audience winner? [08_main_table.csv, 08_added_value.csv, 08_prompt_contrasts.csv]

| Row (clear pairs) | n | Accuracy (95% CI) | Baseline on same pairs | Judge minus baseline (95% CI) | Inconsistency across orders | Picks the first-shown chart |
|---|---|---|---|---|---|---|
| gpt-5 P3 | 250 | 0.636 (0.582-0.690) | 0.584 | +0.052 (-0.028, +0.126) | 0.184 | 0.544 |
| gpt-5 P2 | 150 | 0.600 (0.523-0.667) | 0.520 | +0.080 (-0.023, +0.183) | - | - |
| Gemini 2.5 Flash P1 | 500 | 0.587 (0.552-0.618) | 0.606 | -0.019 (-0.072, +0.036) | - | - |
| gpt-5 title-only (no image) | 500 | 0.582 (0.553-0.612) | 0.606 | -0.024 (-0.074, +0.024) | 0.496 | 0.264 |
| gpt-5 P1 | 500 | 0.579 (0.541-0.616) | 0.606 | -0.027 (-0.083, +0.028) | - | - |
| Haiku 4.5 P3 | 250 | 0.564 (0.512-0.620) | 0.584 | -0.020 (-0.102, +0.064) | 0.184 | 0.416 |
| Gemini 2.5 Flash P3 | 500 | 0.564 (0.533-0.594) | 0.606 | -0.042 (-0.089, +0.007) | 0.532 | 0.766 |
| Haiku 4.5 P1 | 500 | 0.555 (0.520-0.591) | 0.606 | -0.051 (-0.104, +0.002) | - | - |
| Feature baseline (image-blind, OOF) | 500 | 0.606 (0.560-0.646) | - | - | - | - |

- **Every judge beats chance.** Binomial test on decisive pairs: p from 0.03 to 1e-6.
- **No judge beats the image-blind baseline on accuracy.** Every paired CI includes 0, and 6 of 8 point estimates are below the baseline. This triggers the brief's stop-and-check condition on framing.
- **On the same 250 pairs, gpt-5 is equally accurate with P3 (0.636), P1 (0.636) and titles only (0.628).** [08_prompt_contrasts.csv] The P3 row looks best only because those 250 pairs are easier.
- **Judges do add independent signal** on top of the baseline. A logistic model of the baseline's out-of-fold logit plus the judge signal, with a likelihood-ratio test against the baseline alone, gives:
  - gpt-5 P3: LR p = 6e-6, ΔAUC +0.079
  - gpt-5 P2: p = 0.003, ΔAUC +0.097
  - gpt-5 P1: p = 3e-4, ΔAUC +0.035
  - Flash P3: p = 7e-5, ΔAUC +0.038
  - Flash P1: p = 6e-4, ΔAUC +0.030
  - Haiku P3: p = 0.031, ΔAUC +0.022
  - Haiku P1: p = 0.022, ΔAUC +0.012

  So the judges carry real information, about as much as the title and timing features do, and it is partly separate from them.
- **Close pairs** (score ratio 1.5-2.5): all at chance. Flash P1 gets 0.512 (0.462-0.568) and the baseline 0.490.
- **Pointwise** [08_pointwise.csv]: Spearman between P1 and the month percentile is 0.09-0.12 on 1,000 images. After removing the image-blind prediction (partial correlation) it is 0.07-0.09. Note that the images come from extreme pairs, so the month percentiles are bimodal.

**Hypotheses:**
- H1 (accuracy between 50% and 65%): supported for all rows.
- H2 (baseline at 55-60%; judges add a small but significant amount): supported in the added-value sense. The baseline is 59.1% on all 2,000 pairs and 60.6% on the 500 test pairs. The judges add significant log-likelihood but do not raise accuracy significantly.

## RQ2: do rubric prompts agree with the audience more than holistic prompts? [08_prompt_contrasts.csv]

- gpt-5 P2 minus P1 on the same 150 pairs: -0.043 (-0.103, +0.013).
- P3 minus P1, by judge: gpt-5 0.000; Haiku -0.020; Flash -0.023 (-0.054, +0.006).
- **H3 supported:** neither the rubric nor the pairwise format beats holistic scoring.
- Not tested: VisJudge-7B, the expert-aligned model (no GPU). In calibration on VisJudge-Bench all three judges reach r = 0.41-0.47 against expert ratings [05_calibration.csv], yet they agree with the audience only weakly.

## RQ3: where do judges and the audience disagree? [08_breakdowns.csv, 09_disagreement_codes_DRAFT.csv]

- By year: accuracy is lowest in 2012-15 (gpt-5 P1 0.53, n=137; Haiku P1 0.50) and higher from 2016 on (gpt-5 P1 0.59-0.61).
- By chart type, P1: Bar (n=166), Line (112) and Maps (164) all fall between 0.52 and 0.62. gpt-5 P3 reaches 0.68 on Bar and 0.70 on Line. The other types have fewer than 50 pairs each.
- Gallery (gpt-5 P3, 20 confident wrong picks; figures/gallery/wrong_*.jpg). Draft codes from Haiku, **not reviewed by a human**: topic appeal 14, polish over substance 3, novelty or humor 3.
- Visible pattern: the judge's reasons praise labels and clarity, while the audience winner is often a striking chart with little text (e.g. the "world as 100 people" area chart beat a labeled CO2 dashboard).

## RQ4: judge biases [08_bias_probes.csv, figures/fig4_bias_dumbbell.png]

- Logistic coefficients per SD on the A-minus-B feature difference, predicting the audience winner vs the judge's pick.
- **Text amount (log OCR words):** audience -0.04 (SE 0.07); judges +0.34 to +0.95 in all 7 judge rows (gpt-5 P3 +0.37, Haiku P3 +0.95, Flash P3 +0.77). This is the largest and most consistent judge bias. H4's density part is supported for text.
- **Original resolution:** audience +0.14; judges +0.02 to +0.40.
- **Edge density:** the audience prefers lower (-0.21); judges are mixed (-0.57 to +0.14).
- **Color count:** about 0 for both.
- H4's maps part can't be tested this way, because both charts in a pair share the chart type. By type, maps accuracy (0.52-0.60) is close to the other types.
- **Position bias:** Gemini Flash gives different answers in the two orders on 53% of pairs and picks the first-shown chart 77% of the time. gpt-5 and Haiku are inconsistent on 18%.

## Memorization [07_memorization.md, 07_recognition_summary.csv]

- **Cutoffs:** gpt-5 2024-09-30, Haiku 4.5 Feb 2025, Gemini 2.5 Flash Jan 2025. Only gpt-5 has post-cutoff pairs. Its P1 accuracy is 0.581 on 37 post-cutoff pairs vs 0.579 on 463 earlier pairs, and its P3 accuracy is 0.706 on 17 vs 0.631 on 233. No sign of a memorization advantage, but n is small.
- **Recognition probe** (top 50 posts; the brief says 200). The brief's raw rule (a title-match recall rate above 5%) flags Flash (20%) and Haiku (10%). But 72% of these charts print their title in the image. Excluding recalls that match the image's own OCR text leaves 2% / 0% / 2%, so no judge is flagged. The single unexplained hit (2020-03-1046) has a stylized title that OCR probably missed.

## Cost

Total API spend: $8.83 of the $10 cap (`judge_client.total_spend()`, computed from cached token usage at list prices).

## Update 2026-10-09: pre-registered P1 equivalence analysis on all 2,000 clear pairs [08c_equivalence.csv, 08c_accuracy_2000.csv, 08d_non_superiority.csv, 08c_added_value_2000.csv, 08c_bias_probes_2000.csv, 08c_bias_probes_1000.csv, 08c_expert_vs_audience_spearman.csv]

The figures in this section supersede the subset results above for RQ1 and RQ4. See LOG.md for the pre-registration (margin ±4 points, TOST, α = 0.05) and the full numbers.

| P1 judge | n | Acc | Judge minus baseline [90% CI] | Verdict (±4) | p(judge ≥ baseline + 4) |
|---|---|---|---|---|---|
| Baseline | 2,000 | 0.591 | - | - | - |
| gpt-5 | 2,000 | 0.564 | -2.8 [-5.1, -0.3] | inconclusive | 2e-6 |
| Claude Haiku 4.5 | 2,000 | 0.554 | -3.7 [-5.9, -1.3] | inconclusive (significantly worse) | 3e-8 |
| Gemini 2.5 Flash | 2,000 | 0.576 | -1.5 [-3.9, +0.9] | equivalent | 4e-5 |
| Claude Sonnet 5.5 | 1,000 | 0.578 | -1.9 [-5.2, +1.5] | inconclusive | 0.002 |

Total API spend: $28.89.
