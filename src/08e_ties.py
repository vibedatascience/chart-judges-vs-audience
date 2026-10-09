"""Robustness: P1 ties. Judge vs baseline on each judge's decisive pairs (no tie, no failure), paired bootstrap."""
import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
analysis = __import__("08_analysis")
eq = __import__("08c_equivalence")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rng = np.random.default_rng(eq.SEED)
pairs = analysis.load_pairs("clear", eq.N_ALL)
base = analysis.baseline_credit(pairs, "clear")
rows = []
for judge, sc in eq.scored_p1(pairs).items():
    dec = sc[~sc["tie"] & ~sc["failed"]]
    j = dec["credit"].to_numpy()
    b = base.loc[list(dec.index)].to_numpy()
    d = j - b
    lo, hi = eq.boot_mean_ci(d, 0.95, rng)
    rows.append({"judge": judge, "n_pairs": len(sc), "n_decisive": len(dec), "judge_acc_decisive": j.mean(),
                 "baseline_acc_same_pairs": b.mean(), "diff": d.mean(), "ci95_lo": lo, "ci95_hi": hi})
out = pd.DataFrame(rows)
out.to_csv(os.path.join(ROOT, "analysis", "08e_decisive_pairs.csv"), index=False)
print(out.round(4).to_string(index=False))

# Tie-free check: AUC of the judge's score difference vs the baseline's out-of-fold logit, paired bootstrap.
from sklearn.metrics import roc_auc_score
oof = pd.read_csv(os.path.join(ROOT, "analysis", "04_feature_baseline_oof_clear.csv"))
arows = []
for judge, sc in eq.scored_p1(pairs).items():
    m = sc.reset_index()[["a_id", "b_id", "y", "diff", "failed"]].merge(oof[["a_id", "b_id", "baseline_logit"]], on=["a_id", "b_id"])
    m = m[~m["failed"]]
    y, j, b = m["y"].to_numpy(), m["diff"].to_numpy(), m["baseline_logit"].to_numpy()
    aj, ab = roc_auc_score(y, j), roc_auc_score(y, b)
    bs = []
    for _ in range(2000):
        i = rng.integers(0, len(y), len(y))
        if y[i].min() == y[i].max():
            continue
        bs.append(roc_auc_score(y[i], j[i]) - roc_auc_score(y[i], b[i]))
    lo, hi = np.quantile(bs, [0.025, 0.975])
    arows.append({"judge": judge, "n_pairs": len(y), "auc_judge": aj, "auc_baseline": ab, "diff": aj - ab, "ci95_lo": lo, "ci95_hi": hi})
a = pd.DataFrame(arows)
a.to_csv(os.path.join(ROOT, "analysis", "08e_auc_vs_baseline.csv"), index=False)
print(a.round(4).to_string(index=False))
