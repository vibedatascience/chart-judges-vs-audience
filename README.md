# Do LLM chart judges agree with what audiences reward?

Internal research repo (Rahul Chaudhary). A VisNotes-style short paper testing multimodal LLM chart judges against r/dataisbeautiful votes, using the beautiVis dataset.

**Paper:** `paper/main_anon.pdf` (review version), `paper/main_camera.pdf` (camera-ready), `paper/supplement.pdf`.
**Results:** `analysis/results.md`; the full log with every decision, deviation and the pre-registration is in `LOG.md` (summary at the top).

## Headline (pre-registered, 2,000 identical clear pairs, prompt P1)

| Judge | Accuracy | Judge minus baseline [90% CI] |
|---|---|---|
| Image-blind baseline (titles + timing) | 59.1% | - |
| gpt-5 | 56.4% | -2.8 [-5.1, -0.3] |
| Claude Haiku 4.5 | 55.5% | -3.7 [-5.9, -1.3] (significantly worse) |
| Gemini 2.5 Flash | 57.6% | -1.5 [-3.9, +0.9] (TOST-equivalent) |
| Claude Sonnet 5.5 (1,000 pairs) | 57.8% | -1.9 [-5.2, +1.5] |

No judge beats the baseline by 4 points or more (one-sided p ≤ 0.002 for each). Tie-free check: ranked by AUC, every judge is below the baseline (0.571-0.604 vs 0.623-0.630). The same P1 scores correlate ρ = 0.44-0.49 with expert ratings but 0.08-0.13 with audience vote percentile. Judges reward text-heavy charts (+0.32 to +0.51 per SD of OCR words); the audience does not (-0.02).

## Layout

| Path | Contents |
|---|---|
| `src/` | One script per step, run in numeric order (`PYTHONPATH=lib:src python3 src/<step>.py`) |
| `src/prompts.py` | Exact judge prompts |
| `src/judge_client.py` | Cached judge calls to OpenAI, Amazon Bedrock and Google Vertex AI; endpoints are set by environment variables |
| `pairs/` | Evaluation sets (clear 2,000, close 500, dev 100, singles 3,000, calibration 150) |
| `data/clean/` | Cleaned post metadata and per-image features (no images) |
| `judges/raw/`, `judges/parsed/` | Every judge response (raw text, tokens) and parsed scores |
| `analysis/` | All result tables (CSV) and summaries |
| `figures/` | Paper figures; `figures/gallery/` holds the disagreement contact sheets and `coding.html` |
| `paper/` | LaTeX sources (IEEE VGTC conference class) and PDFs |
| `notes/` | Original brief and the prior-work notes |

## Reproducing

```bash
pip install --target lib -r requirements.txt
bash src/00_fetch_osf_images.sh        # beautiVis images from OSF (CC0), about 10.5 GB; not in the repo
PYTHONPATH=lib:src python3 src/01_inventory.py   # ... then 02, 03, 04, 05, 06, 07, 08, 09, 10, 11 in order
```

Not committed, to keep the repo small: `lib/` (pip-installed deps), `tools/` (Tectonic and the VGTC template), raw downloads and images, and `judges/cache/` (the response cache). Without the cache, rerunning the judges calls the APIs again; total spend for all reported runs was $28.89. Every number in the paper can be regenerated from `judges/parsed/` and `analysis/` without API calls.

The paper builds with Tectonic: `cd paper && tectonic -X compile main_anon.tex`.

## Data and licenses

beautiVis metadata is CC0 (Lin et al., PacificVis 2026). The Reddit images belong to their posters and are not redistributed except as small thumbnails in Figure 1 and the internal gallery. VisJudge-Bench declares no license; it is used here for calibration only.

## Open items

- Human coding of the 20 confident misses: open `figures/gallery/coding.html`, fill in `analysis/09_human_codes.csv`, then run `PYTHONPATH=lib:src python3 src/09b_human_coding.py tally`.
