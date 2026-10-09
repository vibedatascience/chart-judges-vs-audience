Agent brief: Do LLM chart judges agree with what audiences reward?

Owner: Rahul Chaudhary. Written 2026-10-08. Target venue: IEEE PacificVis 2027 VisNotes (projected deadline ~2027-01-07, up to 6 pages including references, VGTC format). Backup venue: VISxGenAI 2027 workshop (~2027-08-15).

You are the agent doing this work. Read the whole brief before running anything. Follow the steps in order. Every number you report must come from a file you saved. Keep a running log in LOG.md (date, step, what you did, what you found, open issues).

1. Goal

Multimodal LLMs are now used as judges to score charts that AI agents generate (benchmarks, the AgenticVIS Challenge, product evals). VisJudge-Bench (ICLR 2026) showed these judges agree only moderately with expert ratings (GPT-5 correlation 0.428 on 3,090 charts; their fine-tuned VisJudge-7B reaches 0.687).

Nobody has checked whether these judges agree with what a real audience rewards. r/dataisbeautiful has 13 years of charts with vote counts. The beautiVis dataset packages 50,000+ of them.

This project measures whether LLM judges can pick which of two comparable charts the audience rewarded more, after removing the effects of title, topic, timing and subreddit growth.

Research questions
RQ1. Given two charts posted in the same week with the same chart type, can an LLM judge pick the one the audience rewarded more, better than chance and better than a model that never sees the image?
RQ2. Do expert-aligned judges (VisJudge-7B, VisJudge-style rubric prompts) agree with the audience more or less than plain holistic prompts?
RQ3. Where do judges and the audience disagree: which chart types, which years, which visual properties?
RQ4. What systematic biases do judges show (position, text density, color count, resolution, title presence)?
Hypotheses (write them in LOG.md before running judges, do not edit afterwards)
H1: Pairwise judge accuracy is above 50% but below 65%.
H2: The image-blind baseline (title, timing, chart type) reaches 55-60%. Judges add a small but significant amount on top of it.
H3: Rubric and expert-aligned judges do not beat holistic prompts on audience agreement.
H4: Judges reward visual density and polish more than the audience does. The audience rewards topic novelty and maps more than judges do.
2. Sources to read first (Step 0, about 1 hour)
Source	What to extract into notes/prior_work.md
beautiVis paper, PacificVis 2026 VisNotes. DOI 10.1109/PacificVis68791.2026.00044. Dataset: https://huggingface.co/datasets/sru3/beautiVis	Collection method, filtering, how chart types were labeled, known caveats, license
Beauty in the Eye of AI, EuroVis 2026. DOI 10.1111/cgf.70456	Their human rating protocol, alignment metric, prompts, main numbers. They studied network diagrams only.
VisJudge-Bench, ICLR 2026. https://arxiv.org/abs/2510.22373, data at https://github.com/HKUSTDial/VisJudgeBench, model at https://huggingface.co/xypkent/visjudge-7b	Six rubric dimensions, scale, prompt text (the prompt field in VisJudgeBench.json), reported MAE and correlation per model
How Do LLMs See Charts? EuroVis 2026. DOI 10.1111/cgf.70450	How they compared humans and LLMs on the same stimuli
The Public Life of Data: Investigating Reactions to Visualizations on Reddit. https://arxiv.org/abs/2103.08525	What drives engagement on r/dataisbeautiful; use it to justify the controls

VisJudge-Bench facts already confirmed:

Dimensions: Fidelity (data_fidelity), Expressiveness (semantic_readability, insight_discovery), Aesthetics (design_style, visual_composition, color_harmony).
overall_score is the mean of the six dimensions, on a 1-5 scale.
VisJudge-7B is a LoRA adapter on Qwen/Qwen2.5-VL-7B-Instruct, trained with GRPO. Load the base model in bfloat16, then apply the adapter with PeftModel.from_pretrained.
3. Environment
Python 3.11. Install: huggingface_hub pandas pyarrow numpy scipy scikit-learn statsmodels pillow imagehash opencv-python-headless easyocr matplotlib tqdm tenacity rapidfuzz, plus the official SDKs for each API judge.
API keys come from environment variables. Never write keys into files or logs.
A GPU with 24 GB or more is needed for VisJudge-7B and the open Qwen judge. If you have none, skip those two judges, note it in LOG.md, and continue.
Fixed random seed everywhere: 20261008.

Directory layout:

beautivis-judges/
  LOG.md
  notes/prior_work.md
  data/raw/            # downloaded files, never modified
  data/clean/          # parquet outputs
  data/images_std/     # standardized images sent to judges
  pairs/               # pair and single sets
  judges/raw/          # one JSONL per judge x prompt, raw model output
  judges/parsed/       # parsed scores and picks
  analysis/            # result tables (CSV) and results.md
  figures/
  paper/
  src/                 # all code, one script per step
4. Steps
Step 1. Download and inventory (about 2 hours)
Download the dataset with huggingface_hub.snapshot_download(repo_id="sru3/beautiVis", repo_type="dataset", local_dir="data/raw").
Unzip vis_images.zip only. Do not unzip nonvis_images.zip or combined_images.zip unless needed later.
Load the vis CSV. Expected columns: json_title, json_author, json_created_date, json_url, json_full_permalink, json_score, json_ups, json_downs, json_num_comments, pp_sanitized_title, pp_image_file, gpt_chart_type, gpt_high_level_categories, gpt_cleaned_chart_type, gpt_overarching_chart_type.
Write analysis/01_inventory.md with these tables:
Row count, image files found, and rows whose image file is missing.
Posts per year, with median and p90 score per year.
Posts per gpt_overarching_chart_type.
Score distribution: quantiles 0, 10, 25, 50, 75, 90, 99, 100.
10 sample rows.
Stop and report if vote fields are missing, if fewer than 10,000 chart rows exist, or if the dataset card or paper restricts research use.
Step 2. Clean (about 2 hours)

Apply these filters in order and log how many rows each one removes:

Drop rows with a missing or unreadable image, or a missing score or created date.
Drop rows where gpt_overarching_chart_type is none or Other.
Drop images whose short side is under 300 px.
Drop posts with score < 5. These are usually removed or spam posts. They are not real audience judgments.
Remove near-duplicate images: compute a perceptual hash (imagehash.phash) and treat Hamming distance <= 4 as a duplicate. Keep the earliest post in each duplicate group.

Then:

Standardize images for judges: convert to RGB, resize so the long side is at most 1536 px (keep aspect ratio), and save as JPEG quality 90 in data/images_std/. Every judge receives these exact bytes.
Save data/clean/posts.parquet with a stable post_id (use the image file stem).
Step 3. Build the audience signal and the evaluation sets (about 3 hours)

Raw score is not comparable across time. The subreddit grew many times over between 2012 and 2025, and posting time and title strongly affect votes. Compare charts only against near neighbors.

Month percentile. For each post, compute pct_month = percentile rank of score among all clean posts in the same calendar month (0-1). Also compute z_month = z-score of log1p(score) within the month.
Clear pairs (main test set, 2,000 pairs).
Bucket posts by ISO week x gpt_overarching_chart_type.
Within a bucket, a candidate pair needs score_hi >= 5 * score_lo and score_hi >= 50.
Sample at most 3 pairs per bucket. Use each post in at most one pair across all sets.
Stratify so every year 2012-2025 contributes, and no single chart type is more than 25% of pairs. If 2,000 is not reachable, take all that qualify and log the count.
Randomize which post is shown as "A". Store the true winner.
Close pairs (difficulty set, 500 pairs). Same rules, with a score ratio between 1.5 and 2.5.
Dev set (100 clear pairs). Sampled separately. Use it only for prompt debugging and parser testing. Never report results on it, and never tune anything on the test pairs.
Singles set (3,000 posts). Stratified by year and chart type, not used in any pair. Used for pointwise correlation with pct_month.
Save pairs/clear.parquet, pairs/close.parquet, pairs/dev.parquet and pairs/singles.parquet. Write analysis/03_sets.md with counts by year and chart type for each set.
Step 4. Image-blind baselines (about 3 hours)

These baselines show how much of the audience signal is predictable without seeing the chart. Judges must be compared against them.

Feature baseline. Features per post:
title TF-IDF (word 1-2 grams, min_df 5) and title length in characters;
whether the title contains [OC];
posting hour (UTC) and weekday, both one-hot;
year;
chart type, one-hot.
Pair-level input is the feature difference x_A - x_B. The label is 1 if A won. Model: L2 logistic regression. Evaluate with 5-fold cross-validation grouped by month, so no month appears in both train and test. Save out-of-fold predictions for every pair.
Title-only LLM baseline. Use the strongest API judge with text only: "Two posts were made to r/dataisbeautiful in the same week. Which title got more upvotes? Answer A or B." Run both orders. This measures how much a model can guess from the title alone.
Report accuracy and AUC with 95% bootstrap CIs in analysis/04_baselines.md.
Step 5. Calibrate the judging pipeline on VisJudge-Bench (about 2 hours)

This proves the judge setup is comparable to published work before spending money on the main run.

Sample 300 single_vis items from VisJudgeBench.json with the fixed seed.
Run prompt P2 (below) with each API judge, and with VisJudge-7B if a GPU is available.
Compute Pearson correlation and MAE against overall_score.
Compare with the paper's numbers for any model that appears in both. Stop and report if your correlation for the same model differs from the published one by more than 0.10. That would mean a prompt, parsing or image-handling problem.
Save results to analysis/05_calibration.md.
Step 6. Run the judges (about 1 weekend, mostly waiting)

Judges. Use the latest generally available model in each family, and record the exact model ID string and run date for each:

OpenAI frontier vision model (GPT-5 class)
Anthropic Claude (Sonnet class)
Google Gemini (Pro class)
Qwen/Qwen2.5-VL-7B-Instruct, open weights, GPU
VisJudge-7B, GPU

Settings. Temperature 0, or the provider default if 0 is not supported (log which). Max output 400 tokens. Send the standardized JPEG. Do not send titles unless the prompt says so. Use batch APIs where available. Cache every request by sha256(model_id + prompt_id + image bytes) so reruns cost nothing. Retry with exponential backoff (tenacity, max 5 attempts).

Prompts. Use these exact texts. Store them in src/prompts.py, and treat any edit as a new prompt version recorded in LOG.md.

P1, holistic score (singles set, plus both images of every pair):

You are judging the quality of a data visualization.
Rate this chart from 1 (very poor) to 10 (excellent), considering how clearly it communicates its data, how well it is designed, and how visually appealing it is.
Respond with JSON only: {"score": <integer 1-10>, "reason": "<one sentence>"}

P2, VisJudge-style rubric (same items as P1). For VisJudge-7B, use the prompt field format from VisJudgeBench.json instead:

You are an expert in data visualization. Rate this chart on six dimensions, each from 1 (very poor) to 5 (excellent):
data_fidelity: the visual encoding represents the data accurately without distortion.
semantic_readability: a reader can easily understand what the chart shows.
insight_discovery: the chart helps a reader find meaningful patterns or insights.
design_style: the overall design is professional and consistent.
visual_composition: layout, spacing and hierarchy are well balanced.
color_harmony: colors are harmonious and support the message.
Respond with JSON only: {"data_fidelity": n, "semantic_readability": n, "insight_discovery": n, "design_style": n, "visual_composition": n, "color_harmony": n}

P3, pairwise (clear and close pairs). Two images in one request: first image labeled "Chart A", second labeled "Chart B":

Here are two data visualizations, Chart A and Chart B.
Which one is the better visualization overall, considering clarity, design quality and visual appeal?
Respond with JSON only: {"winner": "A" or "B", "confidence": <integer 1-5>, "reason": "<one sentence>"}

P3-audience, framing variant (clear pairs only):

Both charts were posted to the Reddit community r/dataisbeautiful in the same week.
Which one do you think received more upvotes?
Respond with JSON only: {"winner": "A" or "B", "confidence": <integer 1-5>, "reason": "<one sentence>"}

P3-title, title ablation (500 clear pairs): P3, with each chart's post title placed under its label.

Run plan.

Prompt	Set	Orders	Repeats
P1, P2	singles plus all pair images	n/a	1
P3	clear plus close	A/B and B/A	1
P3	300 clear pairs	A/B and B/A	3 more runs (self-consistency)
P3-audience	clear	both	1
P3-title	500 clear	both	1

Pairwise scoring. For each pair, combine the two orders:

1.0 if both orders pick the true winner;
0.0 if both pick the loser;
0.5 if the two orders disagree (counted as position-dependent).

Report the inconsistency rate separately as the position-bias measure.

Parsing. Parse the JSON strictly. If parsing fails, retry once with "Respond with valid JSON only." If it fails again, record it as a failure. Report the failure rate per judge, and do not silently drop failures.

Budget. Estimate cost from the dev set before the full run and log the estimate. Hard cap of $300 in total API spend. Stop and report before exceeding it.

Step 7. Memorization check (about 2 hours)

Popular posts may be in the training data, which would let a model "remember" the winner.

For each API judge, record its published training cutoff (from official docs; cite the URL in LOG.md).
Split clear pairs into those where both posts predate the cutoff and those where both postdate it. Compare P3 accuracy between the two groups, with CIs. Expect few post-cutoff pairs. Report the n either way.
Recognition probe: take the 200 highest-scored posts in the clean data and ask each judge: "Have you seen this exact chart before? If yes, give its title and approximate year. Respond with JSON: {"seen": true/false, "title": "...", "year": n}". Count a recall when rapidfuzz.fuzz.token_set_ratio(title, true_title) >= 80.
Save to analysis/07_memorization.md. If the recall rate is above 5% for any judge, flag that judge's results as possibly contaminated everywhere they appear.
Step 8. Analysis (about 1 weekend)

All tables go to analysis/ as CSV plus a summary in analysis/results.md. Use 1,000 bootstrap resamples over pairs for every CI.

Main table (RQ1, RQ2). Rows: judge x prompt. Columns: clear-pair accuracy (95% CI), close-pair accuracy, inconsistency rate, parse failure rate, and a binomial test against 0.5. Include both baselines as rows.
Added value over the baseline. Fit a logistic regression on clear pairs using the baseline's out-of-fold logit plus the judge's P1 score difference (A minus B). Report the coefficient, the likelihood ratio test against the baseline-only model, and the change in AUC. Repeat for each judge. This is the key test for RQ1.
Pointwise correlation. On the singles set, report Spearman correlation between pct_month and P1, and between pct_month and the P2 mean, with CIs. Also report the partial correlation after regressing pct_month on the baseline features.
Breakdowns (RQ3). Accuracy by chart type and by year bin (2012-15, 2016-19, 2020-22, 2023-25), with CIs. Mark cells with n < 50 as "too few".
Agreement between judges. Cohen's kappa on P3 picks for each pair of judges. Spearman correlation on P1 scores.
Bias probes (RQ4). Compute these per image:
text amount: easyocr word count;
number of dominant colors: k-means with k up to 12 on downsampled pixels, counting clusters with at least 2% of pixels;
edge density: Canny edges over pixel count;
aspect ratio;
original resolution.
Fit two logistic regressions on clear pairs, both on the feature differences: one predicting the audience winner, one predicting the judge's pick. Compare coefficients side by side. Features with a much larger weight for the judge than for the audience are judge biases.
Framing and title effects. Compare P3 with P3-audience, and P3 with P3-title, using paired bootstrap.
Step 9. Disagreement gallery (about 4 hours)
Using the best judge by clear-pair accuracy, pick:
the 20 clear pairs where the judge picked the loser with confidence >= 4;
the 20 pairs it got right with the highest confidence, as contrast.
Make side-by-side contact sheets in figures/gallery/, with each post's score, month percentile, chart type, title and the judge's one-sentence reason.
Draft a reason code for each disagreement using this codebook:
topic appeal (the audience cared about the subject);
novelty or humor;
map or geographic;
polish over substance (judge rewarded looks);
readability problem the judge missed;
data density;
misleading or questionable encoding;
other.
You may use an LLM to propose codes. Mark every code as draft for human review. Do not present LLM codes as final.
Step 10. Figures (about 3 hours)

One chart per figure. Style: white background, red 
#E60023 for the key series, Navy 
#0a3069 secondary, Teal 
#0d9488 tertiary, Slate 
#64748b neutral. Small label text with no overlaps, and the legend placed outside the plot area. Save as both PNG (300 dpi) and PDF.

Pipeline diagram: data, cleaning, pairing, judges, analysis.
Clear-pair accuracy per judge x prompt as a dot plot with 95% CI bars, a reference line at 0.5, and a band for the feature baseline.
Accuracy by year bin, one line per judge, with the last point labeled.
Bias probe coefficients: dumbbell plot of audience weight vs judge weight per feature.
Gallery figure: 4 disagreement pairs with scores and judge reasons.
Step 11. Deliverables and write-up (about 1 weekend)
analysis/results.md: one section per RQ with the tables, and every number linked to the CSV it came from.
paper/outline.md, a VisNotes outline with a rough page budget:
Introduction (0.5 p): LLM judges are used everywhere; expert agreement is known; audience agreement is not.
Related work (0.5 p): beautiVis, VisJudge-Bench, Beauty in the Eye of AI, How Do LLMs See Charts, Public Life of Data.
Data and pairing (1 p): controls, and why pairs instead of raw scores.
Judges and prompts (0.5 p).
Results (1.5 p): RQ1-RQ4.
Gallery and discussion (1 p): what audiences reward that judges miss.
Limitations (0.25 p): votes are noisy, Reddit is one community, contamination, GPT-4o chart-type labels.
References.
Release plan: code, prompts, post IDs and permalinks, and all judge outputs. Do not redistribute images. The dataset card states no license, so release identifiers only and let others fetch the images from the original dataset.
A final summary for Rahul at the top of LOG.md: 5 bullet findings, the main table, open risks, and what you would do next.
5. Stop and report to Rahul if
Vote fields are missing, or there are fewer than 10,000 clean chart posts.
The beautiVis or VisJudge-Bench license forbids this use.
The VisJudge-Bench calibration differs from published numbers by more than 0.10.
Projected API spend exceeds $300.
No judge beats the feature baseline on clear pairs. This is still a publishable result; check with Rahul before writing so the framing can change.
6. Do not
Do not scrape Reddit live. Scores change over time, so use the dataset snapshot only.
Do not tune prompts, thresholds or pair rules after looking at test results. If a change is needed, document it in LOG.md and rerun everything downstream.
Do not drop parse failures or inconsistent pairs without counting them.
Do not report any number that is not reproducible from saved files by running src/ scripts in order.
Do not include image files in any public release.