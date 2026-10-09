import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd
from rapidfuzz import fuzz

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from judge_client import total_spend  # noqa: E402

run_judges = __import__("06_run_judges")
analysis = __import__("08_analysis")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "analysis")
N_TOP = 50
RECALL_THRESHOLD = 80
CONTAMINATION_FLAG = 0.05
CUTOFFS = {
    "gpt-5": ("2024-09-30", "https://developers.openai.com/api/docs/models/gpt-5"),
    "haiku-4.5": ("2025-02-28", "https://platform.claude.com/docs/en/models/haiku-4-5/overview (reliable Feb 2025; training data Jul 2025)"),
    "gemini-2.5-flash": ("2025-01-31", "https://ai.google.dev/gemini-api/docs/models/gemini-2.5-flash"),
}
PROBE = 'Have you seen this exact chart before? If yes, give its title and approximate year. Respond with JSON: {"seen": true/false, "title": "...", "year": n}'


def probe_one(judge_name: str, pid: str) -> dict:
    model, settings = run_judges.JUDGES[judge_name]
    from judge_client import judge

    r = judge(model, "recognition", [run_judges.image(pid), PROBE], settings)
    m = re.search(r"\{.*\}", r["text"], re.S)
    try:
        obj = json.loads(m.group(0)) if m else {}
    except json.JSONDecodeError:
        obj = {}
    return {"judge": judge_name, "post_id": pid, "raw": r["text"], "seen": obj.get("seen"), "guess_title": obj.get("title", ""), "guess_year": obj.get("year"), "parsed": bool(obj)}


def main() -> None:
    posts = pd.read_parquet(os.path.join(ROOT, "data", "clean", "posts.parquet")).set_index("post_id")
    clear = analysis.load_pairs("clear", analysis.N_CLEAR)
    rows = []
    for judge_name, (cutoff, src) in CUTOFFS.items():
        cut = pd.Timestamp(cutoff)
        created_a = clear["a_id"].map(posts["created"])
        created_b = clear["b_id"].map(posts["created"])
        group = np.where((created_a <= cut) & (created_b <= cut), "pre", np.where((created_a > cut) & (created_b > cut), "post", "straddle"))
        for prompt in ("P1", "P3"):
            for tag in (f"clear{analysis.N_CLEAR}", "clear250", "clear500"):
                recs = analysis.parsed(judge_name, prompt, tag)
                if recs is not None:
                    break
            if recs is None:
                continue
            scored = analysis.score_pointwise(clear, recs, "score") if prompt == "P1" else analysis.score_pairwise(clear[clear.set_index(["a_id", "b_id"]).index.isin(recs.set_index(["a_id", "b_id"]).index)], recs)
            g = pd.Series(group, index=clear.set_index(["a_id", "b_id"]).index)
            scored["cutoff_group"] = g.loc[list(zip(scored["a_id"], scored["b_id"]))].to_numpy()
            for grp, sub in scored.groupby("cutoff_group"):
                c = sub["credit"].to_numpy()
                lo, hi = analysis.boot_ci(c) if len(c) >= 10 else (np.nan, np.nan)
                rows.append({"judge": judge_name, "prompt": prompt, "cutoff": cutoff, "cutoff_source": src, "group": grp, "n_pairs": len(c), "accuracy": c.mean(), "lo": lo, "hi": hi})
    split = pd.DataFrame(rows)
    split.to_csv(os.path.join(OUT, "07_cutoff_split.csv"), index=False)

    top = posts.sort_values("score", ascending=False).head(N_TOP).index.tolist()
    probes = []
    for judge_name in CUTOFFS:
        with ThreadPoolExecutor(8) as ex:
            probes += list(ex.map(lambda p, j=judge_name: probe_one(j, p), top))
    pr = pd.DataFrame(probes)
    pr["true_title"] = pr["post_id"].map(posts["json_title"])
    pr["true_year"] = pr["post_id"].map(posts["year"])
    pr["title_sim"] = [fuzz.token_set_ratio(str(g or ""), t) for g, t in zip(pr["guess_title"], pr["true_title"])]
    pr["recall"] = (pr["seen"] == True) & (pr["title_sim"] >= RECALL_THRESHOLD)  # noqa: E712
    pr.to_csv(os.path.join(OUT, "07_recognition_probe.csv"), index=False)
    summ = pr.groupby("judge").agg(n=("post_id", "size"), claimed_seen=("seen", lambda s: (s == True).mean()), recall_rate=("recall", "mean"), parse_rate=("parsed", "mean")).reset_index()  # noqa: E712
    summ["flag_contaminated"] = summ["recall_rate"] > CONTAMINATION_FLAG
    summ.to_csv(os.path.join(OUT, "07_recognition_summary.csv"), index=False)
    lines = ["# 07 Memorization", "", "## Training cutoffs", ""]
    lines += [f"- {j}: {c} ({s})" for j, (c, s) in CUTOFFS.items()]
    lines += ["", "## Accuracy by cutoff group (clear pairs)", "", split.to_markdown(index=False, floatfmt=".3f"), "",
              f"## Recognition probe: top {N_TOP} posts by score (the brief says 200; reduced for the $10 cap)", "", summ.to_markdown(index=False, floatfmt=".3f"), "",
              f"Recall = seen and token_set_ratio(guessed title, true title) >= {RECALL_THRESHOLD}. Flag if recall rate > {CONTAMINATION_FLAG:.0%}.", "",
              f"Total spend: ${total_spend():.2f}", ""]
    open(os.path.join(OUT, "07_memorization.md"), "w").write("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
