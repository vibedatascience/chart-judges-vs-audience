import os
from collections import Counter, defaultdict

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS = os.path.join(ROOT, "data", "clean", "posts.parquet")
PAIRS_DIR = os.path.join(ROOT, "pairs")
OUT_MD = os.path.join(ROOT, "analysis", "03_sets.md")
SEED = 20261008
MAX_PER_BUCKET = 3
MAX_TYPE_SHARE = 0.25
MIN_HI_SCORE = 50
SETS = [
    ("dev", 100, "clear"),
    ("clear", 2000, "clear"),
    ("close", 500, "close"),
]
N_SINGLES = 3000


def add_audience_signal(df: pd.DataFrame) -> pd.DataFrame:
    month = df["created"].dt.to_period("M")
    df["month"] = month.astype(str)
    df["pct_month"] = df.groupby("month")["score"].rank(pct=True, method="average")
    log_score = np.log1p(df["score"])
    grp = log_score.groupby(df["month"])
    df["z_month"] = (log_score - grp.transform("mean")) / grp.transform("std")
    iso = df["created"].dt.isocalendar()
    df["iso_week"] = iso["year"].astype(str) + "-W" + iso["week"].astype(str).str.zfill(2)
    df["year"] = df["created"].dt.year
    return df


def candidate_pairs(df: pd.DataFrame, kind: str) -> pd.DataFrame:
    rows = []
    pool = df[df["chart_type"].notna()]
    for (week, ctype), grp in pool.groupby(["iso_week", "chart_type"]):
        if len(grp) < 2:
            continue
        ids = grp["post_id"].to_numpy()
        scores = grp["score"].to_numpy()
        hi_idx, lo_idx = np.triu_indices(len(grp), k=1)
        s_i, s_j = scores[hi_idx], scores[lo_idx]
        swap = s_j > s_i
        hi = np.where(swap, lo_idx, hi_idx)
        lo = np.where(swap, hi_idx, lo_idx)
        s_hi, s_lo = scores[hi], scores[lo]
        ratio = s_hi / s_lo
        ok = s_hi >= MIN_HI_SCORE
        ok &= ratio >= 5 if kind == "clear" else (ratio >= 1.5) & (ratio <= 2.5)
        for h, lo_ in zip(hi[ok], lo[ok]):
            rows.append((week, ctype, ids[h], ids[lo_], scores[h], scores[lo_]))
    return pd.DataFrame(rows, columns=["iso_week", "chart_type", "hi_id", "lo_id", "hi_score", "lo_score"])


def select_pairs(cands: pd.DataFrame, n: int, used: set[str], year_of: dict[str, int], rng: np.random.Generator) -> pd.DataFrame:
    cands = cands.iloc[rng.permutation(len(cands))].reset_index(drop=True)
    cands["year"] = cands["hi_id"].map(year_of)
    queues = {y: list(g.index) for y, g in cands.groupby("year")}
    pointers = {y: 0 for y in queues}
    bucket_count: Counter = Counter()
    type_count: Counter = Counter()
    type_cap = int(MAX_TYPE_SHARE * n)
    chosen = []
    active = sorted(queues)
    while len(chosen) < n and active:
        still_active = []
        for y in active:
            if len(chosen) >= n:
                break
            q, i = queues[y], pointers[y]
            picked = False
            while i < len(q):
                r = cands.loc[q[i]]
                i += 1
                bucket = (r["iso_week"], r["chart_type"])
                if r["hi_id"] in used or r["lo_id"] in used:
                    continue
                if bucket_count[bucket] >= MAX_PER_BUCKET or type_count[r["chart_type"]] >= type_cap:
                    continue
                used.update([r["hi_id"], r["lo_id"]])
                bucket_count[bucket] += 1
                type_count[r["chart_type"]] += 1
                chosen.append(q[i - 1])
                picked = True
                break
            pointers[y] = i
            if picked:
                still_active.append(y)
        active = still_active
    out = cands.loc[chosen].reset_index(drop=True)
    a_is_hi = rng.random(len(out)) < 0.5
    out["a_id"] = np.where(a_is_hi, out["hi_id"], out["lo_id"])
    out["b_id"] = np.where(a_is_hi, out["lo_id"], out["hi_id"])
    out["winner"] = np.where(a_is_hi, "A", "B")
    out["score_ratio"] = out["hi_score"] / out["lo_score"]
    return out


def select_singles(df: pd.DataFrame, n: int, used: set[str], rng: np.random.Generator) -> pd.DataFrame:
    pool = df[df["chart_type"].notna() & ~df["post_id"].isin(used)]
    pool = pool.iloc[rng.permutation(len(pool))]
    queues = {y: g["post_id"].tolist() for y, g in pool.groupby("year")}
    ctype = dict(zip(pool["post_id"], pool["chart_type"]))
    type_count: Counter = Counter()
    type_cap = int(MAX_TYPE_SHARE * n)
    chosen = []
    pointers = defaultdict(int)
    active = sorted(queues)
    while len(chosen) < n and active:
        still_active = []
        for y in active:
            if len(chosen) >= n:
                break
            q = queues[y]
            while pointers[y] < len(q):
                pid = q[pointers[y]]
                pointers[y] += 1
                if type_count[ctype[pid]] < type_cap:
                    type_count[ctype[pid]] += 1
                    chosen.append(pid)
                    still_active.append(y)
                    break
        active = still_active
    used.update(chosen)
    return df.set_index("post_id").loc[chosen].reset_index()


def crosstab_md(df: pd.DataFrame, year_col: str, type_col: str) -> str:
    t = pd.crosstab(df[year_col], df[type_col], margins=True, margins_name="total")
    return t.to_markdown()


def main() -> None:
    rng = np.random.default_rng(SEED)
    df = add_audience_signal(pd.read_parquet(POSTS))
    df.to_parquet(POSTS, index=False)
    year_of = dict(zip(df["post_id"], df["year"]))
    cands = {kind: candidate_pairs(df, kind) for kind in ("clear", "close")}
    used: set[str] = set()
    lines = ["# 03 Evaluation sets", ""]
    lines += [f"- Candidate clear pairs (ratio >= 5, hi >= {MIN_HI_SCORE}): {len(cands['clear'])}",
              f"- Candidate close pairs (1.5 <= ratio <= 2.5, hi >= {MIN_HI_SCORE}): {len(cands['close'])}", ""]
    os.makedirs(PAIRS_DIR, exist_ok=True)
    for name, n, kind in SETS:
        sel = select_pairs(cands[kind].copy(), n, used, year_of, rng)
        sel.to_parquet(os.path.join(PAIRS_DIR, f"{name}.parquet"), index=False)
        lines += [f"## {name} ({kind}): {len(sel)} pairs (target {n})", "",
                  f"Winner shown as A: {(sel['winner'] == 'A').mean():.3f}. Median score ratio {sel['score_ratio'].median():.2f}.", "",
                  crosstab_md(sel, "year", "chart_type"), ""]
    singles = select_singles(df, N_SINGLES, used, rng)
    singles.to_parquet(os.path.join(PAIRS_DIR, "singles.parquet"), index=False)
    lines += [f"## singles: {len(singles)} posts (target {N_SINGLES})", "", crosstab_md(singles, "year", "chart_type"), ""]
    lines.append(f"Posts used across all sets: {len(used)} (each at most once).")
    with open(OUT_MD, "w") as f:
        f.write("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
