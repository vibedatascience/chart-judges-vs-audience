"""One-sided half of the pre-registered TOST: H0 judge >= baseline + 4 points."""
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import t as t_dist

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
eqv = __import__("08c_equivalence")
analysis = eqv.analysis

ROOT = eqv.ROOT


def main() -> None:
    pairs = analysis.load_pairs("clear", eqv.N_ALL)
    base = analysis.baseline_credit(pairs, "clear")
    scored = eqv.scored_p1(pairs)
    keys = list(zip(pairs["a_id"], pairs["b_id"]))
    rows = []
    for judge, sc in scored.items():
        ks = keys if eqv.JUDGE_TAGS[judge] == "clear2000" else keys[: eqv.N_FRONTIER]
        d = sc.loc[ks, "credit"].to_numpy() - base.loc[ks].to_numpy()
        se = d.std(ddof=1) / np.sqrt(len(d))
        rows.append({"judge": judge, "n_pairs": len(d), "diff": d.mean(), "p_upper_vs_+4pts": t_dist.cdf((d.mean() - eqv.MARGIN) / se, len(d) - 1),
                     "p_lower_vs_-4pts": 1 - t_dist.cdf((d.mean() + eqv.MARGIN) / se, len(d) - 1)})
    t = pd.DataFrame(rows)
    t.to_csv(os.path.join(ROOT, "analysis", "08d_non_superiority.csv"), index=False)
    print(t.to_string())


if __name__ == "__main__":
    main()
