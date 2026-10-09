"""Build a blind human-coding sheet for the 20 confident misses, and tally it once filled in.

Usage: python3 src/09b_human_coding.py build   -> analysis/09_human_codes.csv (blank) + figures/gallery/coding.html
       python3 src/09b_human_coding.py tally   -> analysis/09_human_codes_summary.csv (+ agreement with LLM drafts)
"""
import os
import sys

import pandas as pd
from sklearn.metrics import cohen_kappa_score

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(ROOT, "analysis")
CODES = ["topic appeal", "novelty or humor", "map or geographic", "polish over substance", "readability problem the judge missed",
         "data density", "misleading or questionable encoding", "other"]
SHEET = os.path.join(A, "09_human_codes.csv")


def build() -> None:
    g = pd.read_csv(os.path.join(A, "09_gallery_pairs.csv"))
    wrong = g[g["kind"] == "wrong"].reset_index(drop=True)
    sheet = pd.DataFrame({"item": range(1, len(wrong) + 1), "winner_id": wrong["winner_id"], "loser_id": wrong["loser_id"],
                          "image": [f"figures/gallery/wrong_{i:02d}.jpg" for i in range(1, len(wrong) + 1)], "your_code": "", "your_note": ""})
    if os.path.exists(SHEET):
        raise SystemExit(f"{SHEET} exists; not overwriting your codes")
    sheet.to_csv(SHEET, index=False)
    rows = "\n".join(f'<h3>Item {r.item}</h3><img src="wrong_{r.item:02d}.jpg" style="max-width:100%">' for r in sheet.itertuples())
    html = f"""<!doctype html><meta charset="utf-8"><title>Code the 20 confident misses</title>
<body style="font-family:sans-serif;max-width:1100px;margin:auto">
<h1>Why did the audience prefer the left chart?</h1>
<p>Each item: left = audience winner, right = the chart gpt-5 preferred in both orders, plus the judge's reason.
Write exactly one code per item in <code>analysis/09_human_codes.csv</code> (column <code>your_code</code>), optional note in <code>your_note</code>.
LLM draft codes are deliberately hidden.</p>
<p><b>Codebook:</b> {" &middot; ".join(CODES)}</p>
{rows}</body>"""
    open(os.path.join(ROOT, "figures", "gallery", "coding.html"), "w").write(html)
    print(f"wrote {SHEET} and figures/gallery/coding.html")


def tally() -> None:
    sheet = pd.read_csv(SHEET).fillna("")
    sheet["your_code"] = sheet["your_code"].str.strip().str.lower()
    bad = sheet[~sheet["your_code"].isin(CODES)]
    if len(bad):
        raise SystemExit(f"items with missing or unknown codes: {bad['item'].tolist()}")
    summary = sheet["your_code"].value_counts().rename_axis("code").reset_index(name="n")
    summary.to_csv(os.path.join(A, "09_human_codes_summary.csv"), index=False)
    draft = pd.read_csv(os.path.join(A, "09_disagreement_codes_DRAFT.csv"))
    m = sheet.merge(draft[["winner_id", "loser_id", "draft_code"]], on=["winner_id", "loser_id"])
    agree = (m["your_code"] == m["draft_code"].str.lower()).mean()
    kappa = cohen_kappa_score(m["your_code"], m["draft_code"].str.lower())
    print(summary.to_string(index=False), f"\nagreement with LLM drafts: {agree:.2f}, Cohen's kappa {kappa:.2f} (n={len(m)})")


if __name__ == "__main__":
    {"build": build, "tally": tally}[sys.argv[1]]()
