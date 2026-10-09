# Prior work: MLLM chart judges vs. r/dataisbeautiful votes (beautiVis)

Compiled 2026-10-08. Only facts read directly from the sources listed are recorded. Where a source was not fully accessible, that is stated. No image data was downloaded.

---

## 1. beautiVis (Lin, Ru, Chang, Bearfield; PacificVis 2026 VisNotes)

- DOI 10.1109/PacificVis68791.2026.00044, IEEE Xplore doc 11558870, pp. 357-362 (Crossref).
- **Access:** I read the full text of the author-hosted PDF (https://seansru.github.io/PacificVis_2026_BeauVis_Short_Paper.pdf, 6 pages). IEEE Xplore did not return content to scripted requests. Semantic Scholar lists the paper as `openAccessPdf.status: CLOSED`. No arXiv version found (arXiv API search "beautiVis" returned nothing).
- Authors are all at Georgia Tech. Kylie Lin and Sean Sheng-tse Ru are co-first authors; Ru's email is sru3@gatech.edu, which explains the "sru3/beautiVis" in the brief.
- **Collection:** covers Feb 2012 (when the subreddit started) to Jan 2025. Posts came from the Arctic-Shift bulk download tool, because the Reddit API returns at most 1000 posts per listing. Posts deleted by users or "removed by moderators for being off-topic, low-quality, or inappropriate" were skipped. The data was processed in monthly batches.
- **Processing:** titles had punctuation and extra whitespace removed (`sanitized_title`). Each image got an ID `yyyy-mm-nnnn`. Only static images were downloaded with BeautifulSoup: the paper says "PNG, JPG, JPEG, or SVG", while the README says PNG/JPG. GIFs and videos were logged and excluded.
- **Labeling:** GPT-4o via the OpenAI Batch API. Each call got the image, the post title and the prompt (local copy: `data/raw/prompt.txt`). The prompt defines "visualization", lists 20 example chart types and 5 non-examples, and returns `chart types; topic keywords`. The list is not a closed set. An image is "nonvis" if its only chart type is "none". The paper reports a cost of about $75-100 for more than 50k images. The first prompt version labeled everything as a non-visualization.
- **Normalization:** GPT-4o produced more than 600 raw chart-type strings. These were cleaned (typos, synonyms), then mapped by GPT-4o into 12 modified MASSVIS categories plus Other.
- **Validation:** 300 stratified images (100 labeled nonvis, 200 labeled vis) were coded by 2 RAs, with disagreements resolved by consensus.
  - Of the 100 nonvis, the RAs judged 7 to be visualizations.
  - Of the 200 vis, 1 was not a visualization and 12 had the wrong chart type.
  - Model-vs-human Cohen's kappa = 0.939.
  - Errors clustered in composites, maps, cartograms, waffle charts and icon arrays.
- **Counts:** 52,836 vis, 10,044 nonvis and 48 corrupt.
  - MASSVIS counts (Table 2): Bar 12,499; Line 11,011; Maps 10,329; Point 5,760; Circle 2,257; Area 2,216; Diagrams 2,008; Grid & Matrix 1,947; Trees & Networks 1,588; Distribution 1,125; Table 38; Text 6; Other 932. The body text says Other = 982, which is internally inconsistent.
  - Top raw chart types: bar 12,253; line 10,660; choropleth 9,497; scatter 3,803; ... network diagram 1,389.
  - Top topics: trends 13,100; geography 6,047; demographics 5,555; united states 4,120.
- **Caveats stated by the authors:**
  - Some images are blurry, incomplete or missing context.
  - GPT-4o produced both false positives and false negatives.
  - Labels use inconsistent terminology and over-specific hybrid names.
  - The subreddit's strict rules shape the sample: source link required, clear unbiased titles, anti-plagiarism, political topics only on Thursdays and personal data only on Mondays. The authors say this means "most posts being removed by moderators" and that many users resubmit.
  - English only, and US-centric.
- **Engagement fields:** the dataset has `score`, `ups`, `downs` and `num_comments`. The paper reports 76,047,285 total upvotes against only 3,908 downvotes across the vis metadata. (Inference, not stated in the paper: `downs` is effectively unusable, and `score`≈`ups`.)
- **Temporal findings:**
  - Topic popularity ranks shift over time. Politics peaked around elections and declined after 2017.
  - Maps were the #1 chart type early on and dropped to #2-3 from 2015.
  - The paper notes `[OC]` posts as a distinct subset. OC creators must post their method, data source and tools in the comments.
- The paper miscites ref [17] (Public Life of Data) as "Kauer, Srinivasan, Bertini". The arXiv authors are Kauer, Ridley, Dörk, Bach.

### Dataset hosting, license, image removal

- **HF** (https://huggingface.co/datasets/beautiVis/beautiVis)
  - Card license: `cc0-1.0`. Task tags: image-classification and image-to-text.
  - Commit history (HF API):
    - 2025-04-28: initial upload. The README was last edited the same day.
    - 2026-02-13 20:23-20:24 UTC: three commits titled only "Delete vis_images.zip" (bb9bd2839c), "Delete nonvis_images.zip" (517153864e) and "Delete combined_images.zip" (739821c970). None of them has a commit message body.
  - The README was not updated and still describes the image zips.
  - Discussions/PRs: **0** (`/api/datasets/beautiVis/beautiVis/discussions` → `count: 0`).
- **OSF** (https://osf.io/pkj7s, public)
  - Node license: **CC0 1.0 Universal** (copyright year 2025, holder blank).
  - The OSF API still lists the image zips, last modified 2025-04-25/26:
    - `vis_images_2012_2019.zip` (3.96 GB), `vis_images_2020_2022.zip` (4.51 GB), `vis_images_2023_2025.zip` (1.98 GB)
    - `nonvis_images.zip` (1.23 GB)
    - `combined_images_{2012_2019,2020_2022,2023_2025}.zip`
    - plus the CSV zips
  - Not downloaded.
- **GitHub** (https://github.com/beautiVis-dataset/beautiVis)
  - **MIT** license.
  - Contains the CSVs and a README. Last push was 2025-04-16; the commits are just "add vis", "remove unneeded files", etc.
- **Reason for removing the HF images: not found.** It is not given in the paper, the HF commits, the HF discussions (none exist), the OSF wiki/metadata or Ru's homepage (https://seansru.github.io/). The paper does not discuss copyright of Reddit-hosted images, and CC0 is asserted over the whole dataset. (Unverified speculation, so treat it as such: the removal could be a rights or Reddit-ToS issue or simply storage. Contact sru3@gatech.edu / cxiong@gatech.edu if it matters.)

---

## 2. "Beauty in the Eye of AI: Aligning LLMs and Vision Models with Human Aesthetics in Network Visualization" (EuroVis 2026, CGF)

- DOI 10.1111/cgf.70456. Crossref authors: Li, Zhang, Wang, Shen, Hu. Affiliations: Northeastern, Bosch AI Research, Ohio State.
  - Version of record license (Crossref): **CC BY-NC 4.0**.
  - The Wiley PDF/XML returned 403 (Cloudflare).
  - **Access:** full text of arXiv v1 2604.03417 (HTML, 3 Apr 2026, arXiv non-exclusive license).
- **Human protocol:**
  - Participants saw 8 layouts of the same graph, one per algorithm: Neato, Kamada-Kawai, FA2, fdp, sfdp, spring, PMDS, spectral. Layouts appeared in a randomized, unlabeled grid. The graphs are all 11,531 from the Rome Graphs collection.
  - Instruction: only "select one drawing you like the most". No aesthetic criteria were given, to avoid bias.
  - The platform used adaptive assignment, prioritizing graphs with 0 or 1 labels and then conflicting graphs.
  - Data was collected May 2022-Aug 2025.
  - Sample sizes are inconsistent in the text:
    - The intro says 27 participants and 64,436 labels.
    - §3 says 25 participants. Two labelers with less than 25% agreement were removed, leaving
      64,222 labels.
    - Graphs got a mean of 5.58 labels (range 3-7). Mean time was 9.59 s per label, for a total of
      172 person-hours.
  - Kamada-Kawai (43.4%) and Neato (34.8%) were chosen most often. Spectral was chosen 0.16% of the time.
- **Alignment metric:** micro-averaged pairwise exact-match rate. For each pair of labelers, it is the fraction of co-labeled graphs where both picked the same layout. For a model, the pairs are model vs. every human.
  - Human-human alignment = **38.34%** (macro-average 38.71%). A random labeler scores 11.5%.
  - Alignment rises to 50.67% when near-identical layouts (Procrustes ≥ 0.95) are merged.
  - Only 5.15% of graphs had unanimous agreement.
  - The target for an AI labeler is to be "indistinguishable from an average human," i.e. about 38%.
- **Prompts:**
  - 0-shot CoT prompt (Table 2): "You are an expert in human aesthetics. ... select the layout that best aligns with human preferences. Let's think step by step. ... 'Reason: Result: layout ?'"
  - Variants: k-shot with images, graph-structure/coordinate features (edgelist, adjacency, Node2Vec, spectral), and a DINOv2/ResNet image-embedding "memory bank".
  - Layout order is randomly permuted per graph.
  - Split: 10,000 train / 1,000 test / 531 val.
- **Main numbers** (test-set alignment %):
  - GPT-4o-mini, image-only: 19.70 (0-shot), 19.52 (1-shot), 18.79 (5-shot). More shots hurt.
  - Best LLM setup: GPT-4o-mini with the DINOv2 memory bank, 1-shot, at 33.11.
  - Same setup with other models: GPT-5 27.80, Gemini 2.5 Flash 14.81, Claude Sonnet 4.5 12.70, Qwen3-235B 11.77.
  - Vision models: a fine-tuned DINOv2-base with soft-multiclass loss reached **36.81**. ResNet-50 reached up to 35.03.
  - Filtering by confidence (LLM label-token probability ≥ 0.45 keeps about 65% of graphs; VM ≥ 0.6 keeps about 76%) brings alignment to the human-human level.
- Relevance to us:
  - Human-human agreement is the ceiling to compare against.
  - Naive image prompting of LLMs was weak. Prompting matters a lot and model rank is not "frontier = best".
  - The comparison was within-stimulus (same graph, different layouts), unlike our cross-post setting.

---

## 3. VisJudge-Bench (Xie et al., ICLR 2026; arXiv 2510.22373)

- **Access:** full text of arXiv HTML v3 (2 Mar 2026). I also read the GitHub README and parsed `VisJudgeBench.json` (annotations only, not images).
- **Data sources and filtering:**
  - Images were web-crawled through search engines: more than 300k images, reduced to 80,210 after hash dedup and filtering.
  - GPT-4o classification plus human verification left 13,220. Stratified sampling then gave **3,090**: 1,041 single, 1,024 multi-view and 1,025 dashboards, across 32 subtypes.
  - The 70/10/20 split gives 2,163 train / 279 val / **648 test**. All models were evaluated on the
    648 test items.
- **Six dimensions** on a 1-5 scale, grouped as "Fidelity, Expressiveness, Aesthetics":
  - Fidelity: Data Fidelity.
  - Expressiveness: Semantic Readability and Insight Discovery.
  - Aesthetics: Design Style ("innovation and uniqueness"), Visual Composition and Color Harmony.
  - Questions and 5-level criteria are rewritten per chart by GPT-4o from templates, using GPT-4o-extracted chart metadata.
- **Annotation:**
  - 603 CloudResearch crowdworkers (88.7% US), paid about $10/h. Each item got 3 raters on all 6 dims.
  - Variance-based conflict detection fed algorithmic resolution suggestions (outlier removal, malicious-score filter, sub-dimension bias correction). Three experts then reviewed all 3,090.
  - About 73% of items kept all original ratings.
  - Crowd-crowd MAE was 0.64-0.70 and crowd-expert MAE was 0.54-0.59. No ICC or alpha is reported.
- **Model evaluation:**
  - Each model returns six 1-5 scores plus reasoning in JSON.
  - Each model was run 3 times and averaged, at temperature 0.8.
  - Metrics: Pearson r, MAE and MSE against the human scores, per dimension and overall.
- **VisJudge:** LoRA plus GRPO on Qwen2.5-VL-7B (also 3B, InternVL3-8B and LLaVA-1.6-7B variants).
  - Reward is exp(-|err|/0.5) plus a format reward.
  - Trained 5 epochs at lr 1e-5.
- **Table 3 (paper v3; identical to the GitHub README).** Columns: Overall, Fidelity, Readability, Insight, Style, Composition, Color.

| Model | MAE overall | r overall | r Fid | r Read | r Ins | r Style | r Comp | r Color |
|---|---|---|---|---|---|---|---|---|
| GPT-5 | 0.553 | 0.428 | 0.255 | 0.439 | 0.382 | 0.463 | 0.276 | 0.295 |
| GPT-4o | 0.610 | 0.482 | 0.381 | 0.539 | 0.442 | 0.471 | 0.277 | 0.363 |
| Claude-4-Sonnet | 0.622 | 0.465 | 0.393 | 0.550 | 0.452 | 0.421 | 0.163 | 0.228 |
| Claude-3.5-Sonnet | 0.824 | 0.395 | 0.325 | 0.492 | 0.365 | 0.455 | 0.137 | 0.259 |
| Gemini-2.5-Pro | 0.662 | 0.265 | 0.178 | 0.379 | 0.353 | 0.445 | 0.193 | 0.208 |
| Gemini-2.0-Flash | 0.682 | 0.395 | 0.372 | 0.459 | 0.417 | 0.459 | 0.157 | 0.209 |
| Qwen2.5-VL-7B | 0.847 | 0.341 | 0.341 | 0.352 | 0.281 | 0.357 | 0.149 | 0.155 |
| Qwen2.5-VL-72B | 0.702 | 0.440 | 0.331 | 0.479 | 0.416 | 0.435 | 0.165 | 0.251 |
| **VisJudge (Qwen2.5-VL-7B)** | **0.421** | **0.687** | 0.574 | 0.628 | 0.576 | 0.568 | 0.513 | 0.385 |

- Other rows: Qwen2.5-VL-3B (MAE 0.821, r 0.272), 32B (0.703, 0.435), InternVL3-8B (0.793, 0.409), LLaVA-1.6-7B (0.724, 0.180). Fine-tuned VisJudge variants: InternVL3-8B (0.541, 0.660), LLaVA (0.496, 0.605), Qwen-3B (0.491, 0.648).
- The **HF model card** (https://huggingface.co/xypkent/visjudge-7b) shows *different, apparently earlier* numbers: VisJudge MAE 0.442 / r 0.681; GPT-5 0.551 / 0.429; Claude-4-Sonnet 0.618 / 0.470; Qwen2.5-VL-7B 1.048 / 0.322. **Cite paper v3**, not the card.
- **Repo** (https://github.com/HKUSTDial/VisJudgeBench): **no license file**. The GitHub API reports `license: null`, and the README has no license section. Last push was 2026-02-04.
  - `VisJudgeBench.json` is **JSONL** with 3,090 lines.
  - Keys: `_id, type, subtype, image_path, overall_score, dimension_scores{data_fidelity, semantic_readability, insight_discovery, design_style, visual_composition, color_harmony}, prompt`.
  - Type counts: single_view 1041, multi_view 1024, dashboard 1025.
  - **There is no train/test split field**, so the 648-item test set cannot be identified from the JSON alone.
  - `overall_score` = mean of the 6 dims (max deviation 0.008). Overall mean is 3.13 (SD 0.72, range 1.0-4.89).
  - Single-view subtypes: bar 176, pie 129, line 100, area 75, treemap 62, sankey 61, heatmap 55, scatter 49, histogram 48, donut 47, funnel 45, bubble 29, choropleth 25, radar 24, network 23, other 22, candlestick 20, gauge 20, box 17, point map 12, violin 1, wordcloud 1.
- **`prompt` format for one single_view item** (`_id` 208, area_chart; abridged, structure exact):

```
You are a rigorous data visualization evaluation expert. You must strictly judge each visualization
based on the "Faithfulness-Expressiveness-Aesthetics" framework and the 1-5 scoring criteria for each metric.
Chart description: <GPT-4o description>
Note: This chart has 6 evaluation metrics across three dimensions, of which 6 use custom scoring criteria.
The evaluation follows the "Faithfulness-Expressiveness-Aesthetics" principle:
- Faithfulness: Data accuracy and truthfulness
- Expressiveness: Information clarity and understandability
- Aesthetics: Visual aesthetics and refinement
For each evaluation question, provide a score from 1 to 5 and a reasoning based on the scoring criteria.
=== FAITHFULNESS ===
Data Fidelity:
Question: <chart-specific question> Please provide a 1-5 score based on the scoring criteria.
Scoring criteria:
  1 points: <...>   ...   5 points: <...>
=== EXPRESSIVENESS ===   (Semantic Readability:, Insight Discovery: — same Question/Scoring criteria shape)
=== AESTHETICS ===       (Design Style:, Visual Composition:, Color Harmony:)
Return ONLY a JSON object with the following format:
{ "data_fidelity": {"score": 1-5, "reasoning": "..."}, ... "color_harmony": {...},
  "average_score": "the average of the above six scores, rounded to 2 decimals" }
Where for each metric, score should be an integer from 1 to 5 ... Do not include any additional text, only the JSON object.
```

  - The JSON uses "Faithfulness" where the paper says "Fidelity".
  - In this item the questions call the chart a "stacked area chart" in the Fidelity and Expressiveness sections but a "stacked bar chart" in the Aesthetics sections, so the per-item rewriting is noisy.
- **VisJudge-7B model:** **Apache-2.0**. It is a PEFT LoRA adapter whose base model is `Qwen/Qwen2.5-VL-7B-Instruct`. The HF repo was last modified 2025-12-17.
- Paper findings relevant to us:
  - Aesthetics is the hardest group: correlations of 0.177-0.408 across the three aesthetic sub-dimensions.
  - Models show systematic score biases (score-distribution analysis, §5.2.2).
  - GPT-4o correlates better than GPT-5 overall (0.482 vs 0.428), even though GPT-5 has lower MAE.

---

## 4. "How Do LLMs See Charts? A Comparative Study on High-Level Visualization Comprehension in Humans and LLMs" (Jeon et al., EuroVis 2026, CGF)

- DOI 10.1111/cgf.70450.
  - Version of record: **CC BY-NC-ND 4.0** (Crossref; Semantic Scholar lists it as HYBRID OA).
  - arXiv 2604.08959 is **CC BY-NC-SA 4.0**.
  - **Access:** full text of the arXiv HTML.
- **Design:**
  - Stimuli are 60 charts reused from prior work (Quadri et al., ref [40]), five per cell of
    3 chart types (bar/line/scatter) × 2 data types (single/multi-class) × 2 compositions (juxtaposed or not).
  - The designs come from professional data journalism, with labels and data **replaced by synthetic data** to remove topic knowledge.
  - The human responses also come from ref [40]: 24 participants answering "Describe what do you see in the graphs".
- **LLMs:** GPT-4o, Claude Sonnet 4 and Gemini 2.5 Flash. Each got the same open question under three length conditions: unconstrained, 2-3 sentences, and 1 sentence.
- **Comparison method (same stimuli, same question):**
  - Each sentence was coded into statistical tasks by GPT-5 as an LLM judge. On a 10% check against
    2 human coders, agreement was 97.3% (Fleiss κ = 0.922).
  - Responses were coded to Bloom's taxonomy level by 6 coders (Krippendorff α = 0.87 on 10%).
  - Visual faithfulness was coded by 3 coders (Gwet AC1 = 0.82): 86.7% fully faithful.
  - Designer-intent match used 4 levels (AC1 = 0.85, κ = 0.74).
  - Cross-condition stability was measured as embedding cosine similarity (text-embedding-3-large).
- **Results:**
  - Humans build trend narratives, while LLMs enumerate comparisons and ranges.
  - LLM strategy is stable across prompt constraints.
  - Complete intent match: LLMs 71.1% (128/180) vs humans 40.6% (117/288).
  - No-match rate: humans 27.1%, LLMs 0%.
- Relevance to us:
  - This is comprehension, not preference. LLM agreement with a "designer" target can coexist with non-human reasoning.
  - The synthetic-label design isolates visuals from topic, which is the confound we face in reverse.

---

## 5. "The Public Life of Data: Investigating Reactions to Visualizations on Reddit" (Kauer, Ridley, Dörk, Bach; CHI 2021)

- arXiv 2103.08525. **Access:** full text of the arXiv HTML.
- **Sample:** the 26 highest-karma r/dataisbeautiful visualization posts from Oct 2019 to Sep 2020. Six that drew mostly off-topic replies were dropped, leaving 20 posts: 9 animated and 11 static.
  - Only top-level comments with at least 5 upvotes were kept, and up to 25 were sampled per post, for 475 comments in total.
  - Comments were coded with Grounded Theory into 10 reaction types (observations, hypotheses, opinions, conclusions, clarifications, proposals, critiques, additional information, testimonies, jokes) and 4 scopes.
  - A follow-up survey got 168 respondents: 58% North America, 45% with some formal data/stats/vis training.
- **Engagement drivers found:**
  - Comment scope was insight 188, topic 187, data 117 and visual representation 82 out of 475.
  - The authors take this as support that "a visualization's subject matter is an important driver for engagement — people engage with topics they are interested in" (citing Kennedy et al.).
  - Some commenters' motivation was "acquir[ing] upvotes" or jokes. Topics clustered on COVID-19, the 2020 US election and pop culture.
- **Limits for our use:**
  - The paper studies *comments*, not post-vote determinants.
  - It does **not** quantify effects of title, posting time or subreddit growth.
  - It supports a topic control directly, and shows that design is a minority of what the audience talks about. Title, timing and growth controls must be justified from other evidence:
    - beautiVis documents day-of-week topic rules (political posts Thursdays, personal data Mondays), strong month-to-month volume variation (its Fig. 2) and topic-rank drift.
    - Our own data can check the rest.

---

## Implications for our design

1. Upvotes mostly measure topic, audience and timing, not chart quality. Control for topic (the beautiVis GPT topics), MASSVIS type, year-month (subreddit growth and volume) and posting weekday/hour (moderation day rules). Compare within strata, or use residualized scores.
2. Use `score` (≈ `ups`); ignore `downs`, which is essentially zero.
3. Removed posts are excluded, so the sample is truncated toward rule-compliant posts. Low-vote posts that survived moderation remain, but report the selection.
4. Prefer within-matched-set comparisons, following the Beauty-in-the-Eye-of-AI design: same month plus same topic and type, then a pairwise or listwise "which got more votes". Report against a noise ceiling, not just against 0. Here the ceiling would come from vote reliability, e.g. duplicates or resubmissions.
5. Expect modest correlations. Even on expert-adjudicated aesthetics, frontier MLLMs reach r ≈ 0.43-0.48 (GPT-5 0.428, GPT-4o 0.482, Claude-4-Sonnet 0.465), and the aesthetics sub-dimensions are lowest.
6. Run titles-vs-no-titles ablations. beautiVis labels used the title, and judges may key on topic via the title or in-image text. "How Do LLMs See Charts" removed topic with synthetic labels.
7. Report Pearson and Spearman, and calibration/bias. Fix temperature and seeds, use repeated sampling (VisJudge used 3 runs at T = 0.8), and randomize option order in pairwise prompts.
8. VisJudge-7B (Apache-2.0 adapter on Qwen2.5-VL-7B) is a legitimate open baseline. Use the VisJudge prompt format, but note that its per-chart questions need GPT-4o-generated chart descriptions.
9. Chart-type labels are GPT-4o outputs (κ = 0.939 on n = 300). Treat them as noisy, especially for composites and maps.
10. Images are no longer on HF. Any image retrieval would come from OSF or the original Reddit/imgur URLs. Check rights and ToS before use or redistribution (see below).

## License summary

| Asset | License (as stated) | Where verified |
|---|---|---|
| beautiVis HF repo (CSVs, prompt; images deleted 2026-02-13) | CC0-1.0 | HF card / API |
| beautiVis OSF project (still lists image zips) | CC0 1.0 Universal | OSF API node_license |
| beautiVis GitHub (CSVs + README) | MIT | GitHub API |
| beautiVis paper | IEEE (closed per S2); author PDF on seansru.github.io | Crossref, S2 |
| Underlying Reddit images | Not addressed by authors; third-party content. CC0 only covers what the affirmer owns (CC0 §4: "disclaims responsibility for clearing rights of other persons") | OSF CC0 text |
| VisJudgeBench repo / JSON / images | **No license declared** (all rights reserved by default) | GitHub API `license: null` |
| VisJudge-7B adapter | Apache-2.0 (base Qwen2.5-VL-7B-Instruct) | HF model card |
| Beauty in the Eye of AI (CGF) | CC BY-NC 4.0 (VoR); arXiv non-exclusive | Crossref, arXiv |
| How Do LLMs See Charts? (CGF) | CC BY-NC-ND 4.0 (VoR); arXiv CC BY-NC-SA 4.0 | Crossref, arXiv |
| Public Life of Data | arXiv preprint (license not checked) | arXiv |
