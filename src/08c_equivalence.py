"""Pre-registered P1 equivalence analysis (LOG.md, 2026-10-09 PRE-REGISTRATION)."""
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import spearmanr, t as t_dist

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
analysis = __import__("08_analysis")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "analysis")
SEED = 20261008
N_BOOT = 10_000
MARGIN = 0.04
N_ALL = 2000
FRESH_FROM = 500
N_FRONTIER = 1000
JUDGE_TAGS = {"gpt-5": "clear2000", "haiku-4.5": "clear2000", "gemini-2.5-flash": "clear2000", "sonnet-5.5": "clear1000"}


def boot_mean_ci(d: np.ndarray, level: float, rng: np.random.Generator) -> tuple[float, float]:
    idx = rng.integers(0, len(d), (N_BOOT, len(d)))
    means = d[idx].mean(axis=1)
    a = (1 - level) / 2
    return float(np.quantile(means, a)), float(np.quantile(means, 1 - a))


def tost(d: np.ndarray, rng: np.random.Generator) -> dict:
    n, m, se = len(d), d.mean(), d.std(ddof=1) / np.sqrt(len(d))
    p_lower = 1 - t_dist.cdf((m + MARGIN) / se, n - 1)
    p_upper = t_dist.cdf((m - MARGIN) / se, n - 1)
    lo90, hi90 = boot_mean_ci(d, 0.90, rng)
    lo95, hi95 = boot_mean_ci(d, 0.95, rng)
    if lo90 > -MARGIN and hi90 < MARGIN:
        verdict = "equivalent"
    elif hi90 < -MARGIN:
        verdict = "worse"
    elif lo90 > MARGIN:
        verdict = "better"
    else:
        verdict = "inconclusive"
    return {"n_pairs": n, "diff": m, "ci90_lo": lo90, "ci90_hi": hi90, "ci95_lo": lo95, "ci95_hi": hi95,
            "tost_p": max(p_lower, p_upper), "superiority_p_two_sided": 2 * min(t_dist.cdf(m / se, n - 1), 1 - t_dist.cdf(m / se, n - 1)),
            "verdict_margin_4pts": verdict}


def scored_p1(pairs: pd.DataFrame) -> dict[str, pd.DataFrame]:
    out = {}
    for judge, tag in JUDGE_TAGS.items():
        recs = analysis.parsed(judge, "P1", tag)
        if recs is None:
            continue
        sub = pairs[pairs["a_id"].isin(recs["post_id"]) & pairs["b_id"].isin(recs["post_id"])]
        out[judge] = analysis.score_pointwise(sub, recs, "score").set_index(["a_id", "b_id"])
    return out


def main() -> None:
    rng = np.random.default_rng(SEED)
    pairs = analysis.load_pairs("clear", N_ALL)
    pairs["pair_index"] = np.arange(len(pairs))
    base = analysis.baseline_credit(pairs, "clear")
    scored = scored_p1(pairs)
    keys = list(zip(pairs["a_id"], pairs["b_id"]))
    subsets = {
        "all 2,000 (primary)": keys,
        "pairs 501-2,000 (fresh)": keys[FRESH_FROM:],
        "first 1,000 (frontier set)": keys[:N_FRONTIER],
    }
    rows, acc_rows = [], []
    for subset, ks in subsets.items():
        b = base.loc[ks].to_numpy()
        acc_rows.append({"subset": subset, "row": "feature baseline (OOF)", "n_pairs": len(ks), "accuracy": b.mean(), **dict(zip(("lo", "hi"), boot_mean_ci(b, 0.95, rng)))})
        for judge, sc in scored.items():
            if not set(ks) <= set(sc.index):
                continue
            c = sc.loc[ks, "credit"].to_numpy()
            acc_rows.append({"subset": subset, "row": f"{judge} P1", "n_pairs": len(ks), "accuracy": c.mean(), **dict(zip(("lo", "hi"), boot_mean_ci(c, 0.95, rng))),
                             "tie_rate": sc.loc[ks, "tie"].mean(), "failure_rate": sc.loc[ks, "failed"].mean()})
            rows.append({"subset": subset, "comparison": f"{judge} P1 minus baseline", **tost(c - b, rng)})
    if "sonnet-5.5" in scored:
        ks = subsets["first 1,000 (frontier set)"]
        s = scored["sonnet-5.5"].loc[ks, "credit"].to_numpy()
        for judge in ("gpt-5", "haiku-4.5", "gemini-2.5-flash"):
            if judge in scored:
                o = scored[judge].loc[ks, "credit"].to_numpy()
                rows.append({"subset": "first 1,000 (frontier set)", "comparison": f"sonnet-5.5 P1 minus {judge} P1", **tost(s - o, rng)})
    eq = pd.DataFrame(rows)
    acc = pd.DataFrame(acc_rows)
    eq.to_csv(os.path.join(OUT, "08c_equivalence.csv"), index=False)
    acc.to_csv(os.path.join(OUT, "08c_accuracy_2000.csv"), index=False)

    scored_flat = {f"{j} P1": sc.reset_index() for j, sc in scored.items() if JUDGE_TAGS[j] == "clear2000"}
    av = analysis.added_value(pairs, scored_flat)
    av.to_csv(os.path.join(OUT, "08c_added_value_2000.csv"), index=False)
    bias = analysis.bias_probes(pairs, scored_flat)
    bias.to_csv(os.path.join(OUT, "08c_bias_probes_2000.csv"), index=False)
    if "sonnet-5.5" in scored:
        frontier = pairs.head(N_FRONTIER)
        bias_f = analysis.bias_probes(frontier, {f"{j} P1": sc.reset_index() for j, sc in scored.items()})
        bias_f.to_csv(os.path.join(OUT, "08c_bias_probes_1000.csv"), index=False)

    posts = pd.read_parquet(os.path.join(ROOT, "data", "clean", "posts.parquet")).set_index("post_id")
    sp_rows = []
    cal = pd.read_csv(os.path.join(OUT, "05_calibration_P1.csv")) if os.path.exists(os.path.join(OUT, "05_calibration_P1.csv")) else None
    for judge, tag in JUDGE_TAGS.items():
        recs = analysis.parsed(judge, "P1", tag)
        if recs is None:
            continue
        ok = recs[recs["status"] == "ok"].set_index("post_id")
        x, y = ok["score"].to_numpy(), posts.loc[ok.index, "pct_month"].to_numpy()
        m = np.column_stack([x, y])
        lo, hi = analysis.boot_ci(m, lambda a: spearmanr(a[:, 0], a[:, 1])[0])
        row = {"judge": judge, "n_audience_images": len(ok), "spearman_P1_vs_audience_pct": spearmanr(x, y)[0], "aud_lo": lo, "aud_hi": hi}
        if cal is not None and judge in set(cal["judge"]):
            c = cal.set_index("judge").loc[judge]
            row.update({"n_expert_items": int(c["n_ok"]), "spearman_P1_vs_expert": c["spearman_P1_vs_expert"]})
        sp_rows.append(row)
    sp = pd.DataFrame(sp_rows)
    sp.to_csv(os.path.join(OUT, "08c_expert_vs_audience_spearman.csv"), index=False)

    pd.set_option("display.width", 250)
    print(acc.round(3).to_string(), "\n")
    print(eq.round(4).to_string(), "\n")
    print(av.round(4).to_string(), "\n")
    print(sp.round(3).to_string(), "\n")
    if len(bias):
        print(bias.pivot(index="feature", columns="target", values="coef").round(3).to_string())


if __name__ == "__main__":
    main()
