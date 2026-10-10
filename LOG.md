# LOG: Do LLM chart judges agree with what audiences reward?

Owner: Rahul Chaudhary. Seed: 20261008. Run code with `PYTHONPATH=lib python3 src/<step>.py` from the project root.

## Summary for Rahul (status 2026-10-09, after the pre-registered rerun; supersedes all earlier summaries)

**The headline comes from the pre-registered P1 analysis on all 2,000 clear pairs.** The earlier subset numbers (60.6% baseline on 500 pairs; gpt-5 P3 at 63.6% on 250) are exploratory and are not to be quoted as results.

**Findings** (analysis/08c_*.csv, 08d_non_superiority.csv)
1. The image-blind baseline (titles and timing) gets 59.1% on 2,000 pairs. P1 judges: gpt-5 56.4%, Haiku 4.5 55.4%, Gemini 2.5 Flash 57.6%; Sonnet 5.5 57.8% on 1,000 pairs, where the baseline is 59.6%.
2. **No judge beats the baseline by 4 points or more** (one-sided p ≤ 0.002 for every judge; upper 90% bounds from -0.3 to +1.5 points). Haiku is significantly *worse* (95% CI [-6.4, -0.9]). Only Flash passes the formal two-sided equivalence test (TOST p = 0.039). Do not write "judges match the baseline."
3. Judges still add independent signal: LR p < 1e-4, ΔAUC +0.010 to +0.026.
4. Same P1 scores, same metric (Spearman): ρ = 0.44-0.49 with expert ratings (150 VisJudge items) vs 0.08-0.13 with audience vote percentile.
5. Text bias: judges +0.32 to +0.51 per SD of OCR word count; audience -0.02 (SE 0.04). Resolution does **not** differ. Position bias: Flash flips its pairwise answer on 53% of pairs (P3, 500 pairs).

**Paper:** paper/main_anon.pdf (for review) and paper/main_camera.pdf (camera-ready), 4 pages, plus paper/supplement.pdf. Title: "Do LLM Chart Judges Agree with What r/dataisbeautiful Upvotes?."

**Open before submission**
- Rahul codes the 20 misses: fill in analysis/09_human_codes.csv using figures/gallery/coding.html, then run `python3 src/09b_human_coding.py tally`.
- Push the release to github.com/vibedatascience/chart-judges-vs-audience (public), after Rahul approves.

**Spend:** $28.89 of the $30 cap.

## Hypotheses (frozen 2026-10-08, before any judge run; do not edit)

- H1: Pairwise judge accuracy is above 50% but below 65%.
- H2: The image-blind baseline (title, timing, chart type) reaches 55-60%. Judges add a small but significant amount on top of it.
- H3: Rubric and expert-aligned judges do not beat holistic prompts on audience agreement.
- H4: Judges reward visual density and polish more than the audience does. The audience rewards topic novelty and maps more than judges do.

## Environment

- Python 3.12.3 (brief says 3.11; no 3.11 in sandbox). Deps installed with `pip --target lib`.
- No GPU in sandbox, so VisJudge-7B and Qwen2.5-VL-7B cannot run here.
- Judge access: OpenAI chat completions, Claude via Amazon Bedrock, Gemini via Google Vertex AI (endpoints set by environment variables; see src/judge_client.py). Probed 2026-10-08: gemini-2.5-pro and gemini-2.5-flash were reachable; Gemini 3.x models were not available to this account, so the Gemini judges are from the 2.5 family.
- Project lived at `~/code/beautivis-judges/` before this repository.

## Entries

### 2026-10-08, Step 0/1: download and inventory

- The brief's repo id `sru3/beautiVis` returns 401 (it does not exist). The real dataset is `beautiVis/beautiVis`, public and not gated. Downloaded `snapshot_download(..., revision=739821c9703a6fa23f64895931b1ccc3a9238f2b)` into `data/raw/`. Unzipped `vis_csv.zip` into `data/vis_csv/`.
- **License:** the dataset card says `cc0-1.0`. The brief assumed no license.
- **Images are gone from HEAD.** Commits on 2026-02-13 deleted `vis_images.zip` (bb9bd2839c), `nonvis_images.zip` (517153864e) and `combined_images.zip` (739821c970). The README still describes them. A HEAD request shows that `resolve/742bbdcb6b/vis_images.zip` still serves 10,460,955,406 bytes. Not downloaded. The reason for deletion is being looked for in Step 0.
- `analysis/01_inventory.md` (src/01_inventory.py):
  - 52,836 rows across 156 monthly CSVs (2012-02 to 2025-01). `pp_image_file` is unique. 0 images on disk.
  - All expected columns are present. No missing scores.
  - `json_ups == json_score` in every row, and `json_downs` is blank in 35k rows. The only vote signal is net score.
  - 10,744 rows (2014-01 to 2015-11 and 2023-04 to 2025-01) have a date without a time of day. In those periods the posting-hour feature in Step 4 is unavailable, so it needs a "missing" level or the hour feature must be dropped.
  - `gpt_overarching_chart_type`: 5,626 empty, 857 "Other", and 3,845 multi-valued (e.g. "Bar, Line"; 221 distinct raw strings). The brief buckets by a single type, so a rule is needed. Proposal: drop multi-valued rows from pairing (n is large enough), or use the first listed type.
  - Score quantiles: median 23, p90 1,482, max 162,617. 10,332 rows have score < 5.
  - Median score per year moves from 6 (2015) to 102 (2024), which confirms the brief's growth and drift concern.
- Rows surviving the metadata-only filters: 46,353 after dropping empty or Other type; 37,257 after also dropping score < 5; 34,120 if multi-valued types are also dropped. Comfortably above the 10,000 stop threshold, before the image filters.

## Open decisions

1. ~~Images~~: resolved, downloaded from OSF with Rahul's approval.
2. Multi-valued chart types: default is to exclude them from pairing (Rahul did not object).
3. Hour of day: default is a "missing" level in the baseline.
4. A GPU for VisJudge-7B and Qwen (needed for RQ2).
5. Gemini: only 2.5-pro is reachable; decide whether to ask for Gemini 3.x access or accept 2.5-pro.

### 2026-10-08, Step 0: prior work (notes/prior_work.md)

- I got the full text of all five papers. The beautiVis PDF is self-hosted at seansru.github.io.
- **Images are still on OSF.** osf.io/pkj7s still lists the image zips (about 4 GB each). No reason for the HF deletion was found: the commits say only "Delete …zip", the HF discussions tab is empty, and the paper says nothing. Contact: sru3@gatech.edu.
- **beautiVis licenses:** CC0 on both HF and OSF, MIT on the GitHub repo (CSVs). The paper does not address rights to the Reddit images, and CC0 does not clear third-party rights, so release identifiers only, as planned.
- The authors hand-checked 300 chart-type labels: Cohen's κ = 0.939. Votes total 76.0M up against 3,908 down, so `downs` is useless, which matches what Step 1 found.
- **VisJudge-Bench:** the GitHub repo and data have **no license** (all rights reserved by default). The VisJudge-7B model is Apache-2.0. The data file is JSONL with no split field, so the paper's 648-item test set can't be rebuilt, and the Step 5 calibration compares a 300-item random sample against test-set numbers. That comparison is approximate; keep the 0.10 tolerance but note this.
- Published overall r for the judges we can use: GPT-5 0.428, Claude-4-Sonnet 0.465, Gemini-2.5-Pro 0.265, VisJudge-7B 0.687, Qwen2.5-VL-7B 0.341. Gemini-2.5-Pro is in the paper, so calibration can check it directly.
- Public Life of Data codes comments, not votes: topic 187, insight 188, design 82. It supports the topic control. The beautiVis rules (politics only on Thursdays, personal data on Mondays) support controlling for weekday.

### 2026-10-08, Step 1b: images

- Rahul approved downloading the images. Source: OSF osf.io/pkj7s (CC0). The files are `vis_images_2012_2019.zip`, `vis_images_2020_2022.zip` and `vis_images_2023_2025.zip`, fetched by `src/00_fetch_osf_images.sh` and checked against OSF's SHA-256 (all OK). They unzip to `data/vis_images/`: 52,836 files, one for every CSV row; 0 failed to open; 0 animated.

### 2026-10-08, Step 2: clean (src/02a_image_quality.py, then src/02_clean.py; output analysis/02_clean.md)

Deviations from the brief. All are decided from image content and titles, never from votes:

1. **New filter, blank images.** 148 images have grayscale std < 2 (96 are pure black). They are black first frames of video posts at 1280x720 or 4096x2160, with titles like "Animated map" and "Timelapse". GPT-4o labeled their chart type from the title alone.
2. **Transparency.** 397 images are more than 5% transparent. The brief's "convert to RGB" leaves the background colour up to the converter (it can come out black), so standardization now puts every image on a white background first.
3. **Duplicate threshold changed from Hamming 4 to 2.** Visual QA (figures/qa/dup_check2.jpg, dup_check3.jpg): every sampled distance-4 pair was a different chart sharing a layout (two pies, two US county maps, two Norway choropleths). Distance 0-2 pairs were real reposts or same-author updates. No distance-3 pairs exist.
4. **New rule for placeholder and template groups.** Some duplicate groups are site link previews or banners (imgur logo, Brandwatch ad, Our World in Data preview), or base-map templates chained together. Rule: a group of 3 or more posts whose median pairwise `token_set_ratio` of titles is < 60 is dropped entirely, not reduced to its earliest post. Result: 120 groups, 534 posts dropped. This also drops some real reposts that have very different titles; the loss is small (1.5%).
5. Known limitation: one-off link previews and banners (e.g. 2020-05-0658, "Wealth shown to scale") are not caught. List this in the paper's limitations.

Counts: 52,836 raw; 52,688 after blank removal; 46,239 after dropping empty or Other chart types; 44,433 after the short-side filter; 35,928 after score >= 5; 34,556 after duplicates. 3,014 multi-type posts stay in `posts.parquet` but are excluded from pairing, leaving 31,542 single-type posts. 5,635 posts have no time of day. Table and Text have only 24 and 3 posts.

### 2026-10-08, Step 3: sets (src/03_sets.py; output analysis/03_sets.md)

- Added `pct_month`, `z_month` (log1p score), `iso_week` and `year` to posts.parquet. The month statistics use all 34,556 clean posts.
- Pairing pool: the 31,542 single-type posts, bucketed by ISO week x chart type. Candidates: 86,867 clear (ratio >= 5, winner >= 50) and 12,538 close (1.5 <= ratio <= 2.5, winner >= 50). The close set also requires winner >= 50 ("same rules").
- Selection: the candidates are shuffled with the seed, then picked round-robin across years (each year takes its next valid pair in turn). That gives equal shares per year wherever posts allow, plus the 25% chart-type cap, at most 3 pairs per bucket per set, and each post used at most once across all sets. Order: dev, then clear, close and singles. Dev is drawn first from the same candidate pool, which the brief's "sampled separately" allows.
- Result: dev 100, clear 2,000, close 500, singles 3,000 (8,200 distinct posts). Every year 2012-2025 appears; 2012 (26 clear pairs) and 2025 (37) are small because few posts exist. Bar, Line and Maps all hit the 500 cap in clear. The share of pairs where A is the winner: clear 0.502, close 0.548, dev 0.540.
- Note: clear pairs are very lopsided (median ratio 31.8), and many losers have scores of 5-10. The losers may include low-effort posts. Check this in the gallery and discuss it in the paper.

### 2026-10-08, Step 4a: feature baseline (src/04_feature_baseline.py; output analysis/04_baselines.md)

- Clear pairs: accuracy 0.591 (95% CI 0.570-0.611), AUC 0.623 (0.601-0.646), n=2000. Close pairs: accuracy 0.504 (0.460-0.550), AUC 0.534 (0.484-0.586), n=500, which is chance.
- Year and chart-type differences are always zero within a pair, so those features do nothing (the brief listed them).
- Implementation choices: TF-IDF is fit inside each fold; C is chosen by inner CV (the brief gave no C); a 'missing' hour level covers the 5,635 date-only posts; folds are grouped by the month of post A.
- The title-only LLM baseline (Step 4b) is deferred until Step 5 picks the strongest API judge.

### 2026-10-08, Budget re-plan: $10 hard cap (Rahul), replacing the brief's $300

- Measured cost per image call on a median image (about 1,200x780 px): gpt-5.4 $0.004, Sonnet 5.5 $0.004, Gemini 2.5 Pro $0.0037, gpt-5 (minimal reasoning) $0.0016, Haiku 4.5 $0.0015, Gemini 2.5 Flash $0.0007. Prices: Claude from the claude-api skill's model table (cached 2026-09-25); OpenAI from https://developers.openai.com/api/docs/pricing; Gemini from https://ai.google.dev/gemini-api/docs/pricing (fetched 2026-10-08). Spend is computed from the token usage cached with each response (`judge_client.total_spend`), and the client stops itself at $9.50.
- Judges available: OpenAI gpt-5.5 and gpt-5.4-mini return 403 under the `openai_dev` policy. gpt-5.4, gpt-5, gpt-5.1, gpt-5.2 and gpt-5-mini work. Gemini 3.x returns 403 (see above).
- **Judges chosen:** gpt-5 (`reasoning_effort=minimal`; the model doesn't accept temperature, so the provider default is used), Claude Haiku 4.5 (`global.anthropic.claude-haiku-4-5-20251001-v1:0`, temperature 0) and Gemini 2.5 Flash (temperature 0, thinking budget 0). Reason: these are three families, gpt-5 is directly comparable with VisJudge-Bench, and the costs fit the cap. Limitation: these are not the newest frontier models.
- **Scope cut:** main test = the first 500 pairs of `pairs/clear.parquet`, which stay balanced by year because selection was round-robin. Fixed before any judge ran on test pairs.
  - P1: all 1,000 images, all 3 judges.
  - P3 (both orders): 250 pairs for gpt-5 and Haiku, 500 pairs for Flash.
  - P2: 250 pairs (500 images), gpt-5 only.
  - Title-only baseline: gpt-5, 500 pairs, both orders.
  - Close set: first 200 pairs, P1 with Flash only.
  - Dropped: P3-audience, P3-title, the self-consistency repeats, the separate singles set (pointwise correlation uses the 1,000 pair images), VisJudge-7B and Qwen (no GPU), and the memorization recognition probe except a small one if budget remains.
- Image resolution stays at the brief's 1536 px long side.
- Client: interleaved parts for P3 (`"Chart A:", imgA, "Chart B:", imgB, prompt`). The gateways rate-limit at 50 requests/min per host (HTTP 429 seen on Vertex), so a client-side limiter caps each host at 45/min, and retries were raised from 5 to 8 attempts with backoff of 5-90 s (the brief says max 5).
- Dev check (20 dev pairs P1, 10 dev pairs P3, per judge): every call parsed, after fixing the 429 handling. Dev results are not reported.

### 2026-10-08, Step 5: calibration (src/05a_fetch_visjudge.py, src/05_calibrate.py; analysis/05_calibration.md)

- 150 `single_view` items (the brief says `single_vis`; the actual type name is `single_view`), seed 20261008, P2, judge score = mean of the 6 dimensions.
- gpt-5: r = 0.414 (95% CI 0.262-0.537), MAE 0.622. Published GPT-5: r 0.428, MAE 0.553. |Δr| = 0.014 < 0.10, so **PASS**. Caveat: we sampled single-view items only and the published set is the 648-item test split over all types, so the comparison is approximate (the split can't be rebuilt).
- Haiku 4.5: r = 0.467 (0.326-0.590), MAE 0.692. Gemini 2.5 Flash: r = 0.472 (0.319-0.599), MAE 0.871. Neither model is in the paper; both are near the published Claude-4-Sonnet (0.465) and Gemini-2.0-Flash (0.395).
- 0 parse failures. Calibration cost $0.60. Total spend $0.87.

### 2026-10-08/09, Steps 6-10: main run and analysis

- Runs: `src/06_main_run.sh`, then `src/04b_title_baseline.py` and P2 on 150 pairs (`judges/run_openai2.log`). 0 parse or API failures across all tasks.
- **P2 cut from 250 to 150 pairs mid-run.** P3 cost about 40% more than the dev estimate (Haiku P3 $1.36, gpt-5 P3 $1.20), and 250 pairs would have pushed the total near the $9.50 hard stop. The choice was made on cost alone, before any P2 result was seen.
- A `pkill` pattern also killed the launcher and the title-only process. Title-only was rerun; responses already made were cached and not paid twice.
- Analysis: `src/08_analysis.py` and `src/08b_prompt_contrasts.py`; results in `analysis/results.md`. Judge-vs-baseline comparisons are paired on the same pairs, because P3 and P2 ran on subsets.
- Image features (`src/08a_image_features.py`) were computed for the 1,000 clear test images (plus 100 close images); the job was stopped after that because the close set wasn't needed for the bias probes.
- Memorization (`src/07_memorization.py`, `src/07b_recognition_ocr_control.py`): the recognition probe used the top 50 posts, not 200. **Added an OCR control:** recalls whose guessed title matches the chart's own OCR text don't count as memory. Raw rule: Flash 20%, Haiku 10%, gpt-5 2%. With the control: 2%, 2%, 0%, so nothing is flagged.
- Gallery (`src/09_gallery.py`): best judge = gpt-5 P3. 20 wrong picks (both orders wrong, mean confidence >= 4) and 20 right ones are in `figures/gallery/`. Draft codes by Haiku 4.5 are in `analysis/09_disagreement_codes_DRAFT.csv` (DRAFT, human review needed).
- Figures (`src/10_figures.py`): fig1-fig4 as PNG and PDF. Fig 2's baseline band is for all 500 pairs; use the paired diffs in the table for subset rows.
- **STOP condition hit:** no judge beats the feature baseline on clear pairs. Waiting for Rahul on framing before Step 11.
- Final API spend: $8.83.

### 2026-10-09, Step 11: paper draft (paper/main.tex -> paper/main.pdf)

- Rahul approved the framing ("judges agree with experts, not audiences") and asked for the paper with real examples.
- Format: IEEE VGTC conference class (`ieeevgtc/vgtc_conference_latex`, main branch), compiled with Tectonic 0.17.0 (`tools/`). 4 pages including references, within the VisNotes limit of 6.
  - Body font is TeX Gyre Termes: the class's `times` package doesn't work under XeTeX.
  - The teaser caption is typeset by hand: `\caption` inside `\teaser` printed empty with this toolchain.
- Figures:
  - Teaser `fig5_examples` (src/10b_example_figure.py): 4 of gpt-5 P3's confident misses (wrong in both orders), with verbatim AB-order reasons; "Chart A/B" is replaced by a bracketed referent.
  - `fig6_paired_diff`: judge minus baseline on the same pairs.
  - `fig4_bias_dumbbell`, rebuilt at column width.
  - Table 1 from 08_main_table.csv and 08_added_value.csv.
- References (7): metadata from Crossref or the arXiv API, not from memory.
- The paper shows 8 Reddit images, credited by user and post ID. **Check before any public posting:** this is commentary use, but the release plan still excludes image files.
- Fixes found while re-checking the paper against the CSVs: the task count is 7,150 (I had written 6,450 in results.md), and the chart-type accuracy range of 52-62% holds for P1 only.
- Submission notes: the author block is not anonymized (check PacificVis's review policy). `\onlineid` is 0.

### 2026-10-09, PRE-REGISTRATION: P1 equivalence rerun (written before any new judge call; do not edit)

Context: Rahul's review says the null rests on 150-500 pairs and different subsets. The new budget cap is $30 total, which I read from "about 2-3x the current $10" ($8.83 spent so far).

- **Primary analysis:** prompt P1 (unchanged from src/prompts.py) on **all 2,000 pairs of pairs/clear.parquet**, for gpt-5, Claude Haiku 4.5 and Gemini 2.5 Flash, with the same settings as before. Pair credit is the same as before: 1 if the winner has the higher score, 0.5 on a tie or a failure, 0 otherwise.
- **Comparator:** the image-blind feature baseline's out-of-fold predictions (analysis/04_feature_baseline_oof_clear.csv, computed 2026-10-08 and not refit).
- **Equivalence test:** TOST on the paired per-pair accuracy difference (judge minus baseline) with **margin ±4 accuracy points**, α = 0.05.
  - Decision rule: the judge is equivalent to the baseline if the 90% CI of the mean paired difference lies entirely inside (-4, +4) points. CI method: paired bootstrap, 10,000 resamples over pairs, seed 20261008. Analytic paired t-based TOST p-values are reported alongside.
  - If the 90% CI lies entirely below -4, report "worse than the baseline"; entirely above +4, "better"; otherwise "inconclusive".
  - A superiority test is also reported (two-sided 95% CI of the same difference).
- **Robustness check:** the same analysis on pairs 501-2,000 only (the 1,500 pairs no judge had been run on before today).
- **Frontier judge:** Claude Sonnet 5.5 (`global.anthropic.claude-sonnet-5-5`), P1 only, on **the first 1,000 clear pairs** (2,000 images); the budget can't cover all 2,000.
  - Settings: effort "low", adaptive thinking (the model can't turn thinking off), and no temperature parameter (non-default values return a 400).
  - It gets the same TOST against the baseline on those 1,000 pairs, and paired comparisons with the other three judges on the same pairs.
- **Secondary analyses** (same 2,000 pairs, P1): the added-value likelihood-ratio test and the text/OCR bias probe. Bias features need OCR on the 3,000 new images.
- **Nothing else changes:** prompts, pair sets, image preprocessing and judge settings for the three existing judges all stay as they were.
- **Budget mechanics:** `HARD_STOP_USD` is raised to 29.20. Spend is now re-read from disk every 50 new calls, so parallel processes see each other's spend.
- **Addition, logged before any rerun result was seen:** P1 on the 150 VisJudge-Bench calibration items for all 4 judges (about $0.80). This lets the expert-vs-audience contrast use the same prompt and the same metric (Spearman of the P1 score with expert overall_score vs with the audience month percentile). It addresses the review point that Spearman 0.09-0.12 against Pearson 0.41-0.47 compared different metrics and different prompts.
- **Change to the addition above, logged before running it:** Sonnet 5.5 cost about 15% more per image than its smoke test showed. Total spend after the rerun is about $28.35, and P1 calibration for all 4 judges (about $1.00) would cross the $29.20 hard stop. P1 calibration therefore runs for gpt-5, Haiku 4.5 and Gemini 2.5 Flash only (about $0.57). Sonnet 5.5's expert agreement is not measured.

### 2026-10-09, RESULTS of the pre-registered P1 rerun (src/06c_p1_rerun.sh, src/08c_equivalence.py, src/08d_non_superiority.py)

- Runs: gpt-5, Haiku 4.5 and Flash P1 on all 4,000 images (2,000 pairs); Sonnet 5.5 P1 on 2,000 images (first 1,000 pairs). 1 parse failure in 14,000 calls (Haiku), counted as a tie. P1 calibration on 150 VisJudge items for 3 judges.
- **Final API spend: $28.89** (cap $30).
- Primary (all 2,000 pairs; baseline 0.591). Judge minus baseline, 90% CI, and the verdict under the pre-registered ±4 rule:
  - gpt-5: -2.75 [-5.10, -0.32], inconclusive (could be worse by more than 4).
  - Haiku: -3.65 [-5.90, -1.32], inconclusive; significantly worse (95% CI [-6.35, -0.88]).
  - Flash: -1.52 [-3.85, +0.85], **equivalent** (TOST p = 0.039).
  - Sonnet 5.5 (1,000 pairs; baseline 0.596): -1.85 [-5.20, +1.45], inconclusive. It is equivalent to gpt-5 (TOST p = 0.004) and to Flash (p = 0.002).
- The one-sided upper half of the TOST (H0: judge >= baseline + 4) is rejected for all four judges: p = 2e-6, 3e-8, 4e-5 and 0.002.
- Fresh pairs 501-2,000: -2.77, -3.17 and -1.40. Same direction; all inconclusive under the two-sided rule.
- Added value at n = 2,000: LR chi² 32.7 / 17.1 / 39.5, all p < 1e-4; ΔAUC +0.022 / +0.010 / +0.026.
- Same metric for experts vs audience (P1 Spearman): experts 0.442 / 0.489 / 0.453 (gpt-5 / Haiku / Flash) vs audience 0.084 / 0.115 / 0.133 (Sonnet 0.119).
- Bias at n = 2,000 (OCR words, per SD): audience -0.017 (SE 0.038); gpt-5 +0.498, Haiku +0.473, Flash +0.315; Sonnet +0.514 on 1,000 pairs. **Resolution no longer differs** between judges and audience (0.14-0.21 vs 0.18), so that claim is dropped.
- Figure 1 pairs: all 4 judges score the audience loser higher in 15 of 16 judge-pair cases (1 tie).

### 2026-10-09, Paper v2 (paper/main.tex -> main.pdf, 4 pages; paper/supplement.pdf, 4 pages; v1 kept as paper/main_v1_2026-10-09.tex)

- Revised after Rahul's review:
  - New title around the measured gap.
  - The primary result is the pre-registered P1 TOST on identical pairs.
  - A frontier judge is added.
  - The expert-vs-audience comparison uses the same prompt and metric.
  - P2, P3 accuracy, close pairs, calibration and memorization moved to the supplement (generated by src/11_supplement.py from CSVs).
  - Added related work: Panda 2026 (arXiv 2606.10095) and Seto et al. 2026 (arXiv 2606.15136), both verified on arXiv.
- New figures: fig7_tost (equivalence test), fig8_bias_all (5 features × audience + 4 judges), and fig5_examples (P1 scores from all 4 judges added).
- Open: "audiences reward topics" in the title rests on indirect evidence, which the limitations section states. Human review of the reason codes would strengthen it.

### 2026-10-09, post-hoc tie check and paper polish (src/08e_ties.py)

- P1 ties on 22.8-35.3% of pairs and a tie earns 0.5, so two tie-free checks were added after the pre-registered analysis. They are labeled post hoc in the paper.
- Decisive pairs only (analysis/08e_decisive_pairs.csv): judge minus baseline on the same pairs is gpt-5 -1.0 [-4.5, +2.4], Haiku -1.6 [-5.3, +2.0], Flash +3.3 [-0.3, +7.1], Sonnet 0.0 [-4.9, +4.9] (95% CIs). None is significant. Flash's upper bound passes +4, so the paper states that the four-point bound holds under the pre-registered scoring but not on Flash's decisive pairs alone.
- AUC, no tie rule (analysis/08e_auc_vs_baseline.csv): judge minus baseline is gpt-5 -0.042 [-0.075, -0.007], Haiku -0.052 [-0.086, -0.019], Flash -0.021 [-0.055, +0.014], Sonnet -0.027 [-0.074, +0.022].
- Paper corrections: the upper 90% bounds range from -1.3 to +1.5 points (the draft said -0.3); Flash's text coefficient is +0.31 (the draft said +0.32); accuracies use half-up rounding (Haiku 55.5%).
- Figures 2 and 3 restyled: red = judge, navy = audience, as in Figure 1. The P1 prompt is now printed verbatim in the paper.
