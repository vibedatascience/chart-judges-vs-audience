import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
analysis = __import__("08_analysis")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTRASTS = [("gpt-5 P2", "gpt-5 P1"), ("gpt-5 P3", "gpt-5 P1"), ("haiku-4.5 P3", "haiku-4.5 P1"), ("gemini-2.5-flash P3", "gemini-2.5-flash P1"), ("gpt-5 P3", "gpt-5 title-only")]


def main() -> None:
    scored = {}
    for path in os.listdir(analysis.OUT):
        if path.startswith("08_scored__"):
            name = path[len("08_scored__"):-4].replace("__", " ")
            scored[name] = pd.read_csv(os.path.join(analysis.OUT, path))
    rows = []
    for a, b in CONTRASTS:
        m = scored[a][["a_id", "b_id", "credit"]].merge(scored[b][["a_id", "b_id", "credit"]], on=["a_id", "b_id"], suffixes=("_a", "_b"))
        d = (m["credit_a"] - m["credit_b"]).to_numpy()
        lo, hi = analysis.boot_ci(d)
        rows.append({"contrast": f"{a} minus {b}", "n_pairs": len(m), "acc_a": m["credit_a"].mean(), "acc_b": m["credit_b"].mean(), "diff": d.mean(), "lo": lo, "hi": hi})
    t = pd.DataFrame(rows)
    t.to_csv(os.path.join(analysis.OUT, "08_prompt_contrasts.csv"), index=False)
    print(t.round(3).to_string())


if __name__ == "__main__":
    main()
