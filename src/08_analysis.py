import glob
import os
import sys

import numpy as np
import pandas as pd
import scipy.sparse as sp
import statsmodels.api as sm
from scipy.stats import binomtest, chi2, spearmanr
from sklearn.linear_model import RidgeCV
from sklearn.metrics import cohen_kappa_score, roc_auc_score

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
fb = __import__("04_feature_baseline")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARSED = os.path.join(ROOT, "judges", "parsed")
OUT = os.path.join(ROOT, "analysis")
SEED = 20261008
N_BOOT = 1000
N_CLEAR = 500
N_CLOSE = 200
MIN_CELL = 50
YEAR_BINS = [(2012, 2015, "2012-15"), (2016, 2019, "2016-19"), (2020, 2022, "2020-22"), (2023, 2025, "2023-25")]
BIAS_FEATURES = ["log_ocr_words", "n_colors", "edge_density", "log_aspect_ratio", "log_orig_megapixels"]
rng = np.random.default_rng(SEED)


def boot_ci(values: np.ndarray, stat=np.mean) -> tuple[float, float]:
    n = len(values)
    stats = [stat(values[rng.integers(0, n, n)]) for _ in range(N_BOOT)]
    return float(np.percentile(stats, 2.5)), float(np.percentile(stats, 97.5))


def load_pairs(name: str, n: int) -> pd.DataFrame:
    p = pd.read_parquet(os.path.join(ROOT, "pairs", f"{name}.parquet")).head(n).copy()
    p["winner_id"] = np.where(p["winner"] == "A", p["a_id"], p["b_id"])
    p["y"] = (p["winner"] == "A").astype(int)
    return p


def parsed(judge: str, prompt: str, tag: str) -> pd.DataFrame | None:
    path = os.path.join(PARSED, f"{judge}__{prompt}__{tag}.csv")
    return pd.read_csv(path) if os.path.exists(path) else None


def score_pointwise(pairs: pd.DataFrame, recs: pd.DataFrame, col: str) -> pd.DataFrame:
    """Pair credit from pointwise scores: 1 if the winner scored higher, 0.5 on a tie or a failure, 0 otherwise."""
    s = recs.set_index("post_id")[col].where(recs.set_index("post_id")["status"] == "ok")
    out = pairs.copy()
    out["s_a"], out["s_b"] = out["a_id"].map(s), out["b_id"].map(s)
    out["failed"] = out["s_a"].isna() | out["s_b"].isna()
    diff = (out["s_a"] - out["s_b"]).fillna(0)
    out["diff"] = diff
    signed = np.sign(diff) * np.where(out["y"] == 1, 1, -1)
    out["credit"] = np.where(out["failed"], 0.5, (signed + 1) / 2)
    out["tie"] = (diff == 0) & ~out["failed"]
    out["inconsistent"] = np.nan
    out["judge_pick_a"] = np.where(out["failed"] | out["tie"], np.nan, (diff > 0).astype(float))
    return out


def score_pairwise(pairs: pd.DataFrame, recs: pd.DataFrame) -> pd.DataFrame:
    """Combine the AB and BA orders: 1 both right, 0 both wrong, 0.5 if they disagree or either order failed."""
    recs = recs.copy()
    other = np.where(recs["shown_first"] == recs["a_id"], recs["b_id"], recs["a_id"])
    recs["chosen"] = np.where(recs["status"] != "ok", None, np.where(recs["pick"] == "A", recs["shown_first"], other))
    wide = recs.pivot_table(index=["a_id", "b_id"], columns="order", values="chosen", aggfunc="first").reset_index()
    conf = recs.pivot_table(index=["a_id", "b_id"], columns="order", values="confidence", aggfunc="first").reset_index() if "confidence" in recs else None
    out = pairs.merge(wide, on=["a_id", "b_id"], how="left")
    for o in ("AB", "BA"):
        if o not in out:
            out[o] = None
    out["failed"] = out["AB"].isna() | out["BA"].isna()
    right_ab = out["AB"] == out["winner_id"]
    right_ba = out["BA"] == out["winner_id"]
    out["credit"] = np.where(out["failed"], 0.5, (right_ab.astype(float) + right_ba.astype(float)) / 2)
    out["inconsistent"] = np.where(out["failed"], np.nan, (out["AB"] != out["BA"]).astype(float))
    out["tie"] = False
    pick_a = (out["AB"] == out["a_id"]).astype(float) + (out["BA"] == out["a_id"]).astype(float)
    out["diff"] = np.where(out["failed"], 0.0, pick_a - 1)
    out["judge_pick_a"] = np.where(out["failed"] | (out["inconsistent"] == 1), np.nan, (pick_a == 2).astype(float))
    if conf is not None:
        out = out.merge(conf.rename(columns={"AB": "conf_AB", "BA": "conf_BA"}), on=["a_id", "b_id"], how="left")
    return out


def baseline_credit(pairs: pd.DataFrame, set_name: str) -> pd.Series:
    oof = pd.read_csv(os.path.join(OUT, f"04_feature_baseline_oof_{set_name}.csv"))
    m = pairs[["a_id", "b_id", "y"]].merge(oof[["a_id", "b_id", "baseline_logit"]], on=["a_id", "b_id"], how="left")
    return pd.Series(np.where(m["baseline_logit"] > 0, m["y"], 1 - m["y"]).astype(float), index=pd.MultiIndex.from_frame(m[["a_id", "b_id"]]))


def paired_vs_baseline(scored: pd.DataFrame, set_name: str) -> dict:
    base = baseline_credit(scored, set_name)
    b = base.loc[list(zip(scored["a_id"], scored["b_id"]))].to_numpy()
    d = scored["credit"].to_numpy() - b
    lo, hi = boot_ci(d)
    return {"baseline_acc_same_pairs": b.mean(), "diff_vs_baseline": d.mean(), "diff_lo": lo, "diff_hi": hi}


def first_shown_rate(recs: pd.DataFrame) -> float:
    ok = recs[recs["status"] == "ok"]
    return float((ok["pick"] == "A").mean()) if "pick" in ok and len(ok) else np.nan


def summarize(name: str, scored: pd.DataFrame, n_tasks_failed: int, n_tasks: int) -> dict:
    c = scored["credit"].to_numpy()
    lo, hi = boot_ci(c)
    k_right, k_wrong = int((c == 1).sum()), int((c == 0).sum())
    p = binomtest(k_right, k_right + k_wrong, 0.5).pvalue if k_right + k_wrong else np.nan
    return {
        "row": name, "n_pairs": len(scored), "accuracy": c.mean(), "acc_lo": lo, "acc_hi": hi,
        "decisive_right": k_right, "decisive_wrong": k_wrong, "binom_p_vs_0.5": p,
        "inconsistency_rate": np.nanmean(scored["inconsistent"]) if scored["inconsistent"].notna().any() else np.nan,
        "tie_rate": scored["tie"].mean(), "parse_or_api_failure_rate": n_tasks_failed / n_tasks if n_tasks else np.nan,
    }


def collect(pairs: pd.DataFrame, set_tag: str) -> dict:
    """Return {row_name: (scored_pairs, recs)} for every judge x prompt available on this set."""
    rows = {}
    for path in sorted(glob.glob(os.path.join(PARSED, f"*__{set_tag}.csv"))):
        judge, prompt, _ = os.path.basename(path)[:-4].split("__")
        recs = pd.read_csv(path)
        if prompt in ("P1", "P2"):
            col = "score" if prompt == "P1" else "p2_mean"
            sub = pairs[pairs["a_id"].isin(recs["post_id"]) & pairs["b_id"].isin(recs["post_id"])]
            rows[f"{judge} {prompt}"] = (score_pointwise(sub, recs, col), recs)
        elif prompt in ("P3", "title-only"):
            sub = pairs[pairs.set_index(["a_id", "b_id"]).index.isin(recs.set_index(["a_id", "b_id"]).index)]
            rows[f"{judge} {prompt}"] = (score_pairwise(sub, recs), recs)
    return rows


def main_table(clear: pd.DataFrame, close: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    rows = []
    scored_clear = {}
    for tag, pairs, n in ((f"clear{N_CLEAR}", clear, N_CLEAR), ("clear250", clear.head(250), 250), ("clear150", clear.head(150), 150), (f"close{N_CLOSE}", close, N_CLOSE)):
        for name, (sc, recs) in collect(pairs, tag).items():
            failed = int((recs["status"] != "ok").sum())
            r = summarize(name, sc, failed, len(recs))
            r["set"] = "close" if tag.startswith("close") else "clear"
            r.update(paired_vs_baseline(sc, r["set"]))
            r["picks_first_shown_rate"] = first_shown_rate(recs) if ("P3" in name or "title-only" in name) else np.nan
            rows.append(r)
            if r["set"] == "clear":
                scored_clear[name] = sc
    oof = pd.read_csv(os.path.join(OUT, "04_feature_baseline_oof_clear.csv"))
    base = clear.merge(oof[["a_id", "b_id", "baseline_logit"]], on=["a_id", "b_id"])
    base_credit = np.where(base["baseline_logit"] > 0, base["y"], 1 - base["y"]).astype(float)
    base_sc = base.assign(credit=base_credit, inconsistent=np.nan, tie=False)
    r = summarize("feature baseline (OOF)", base_sc, 0, 0)
    r["set"] = "clear"
    rows.append(r)
    oof_close = pd.read_csv(os.path.join(OUT, "04_feature_baseline_oof_close.csv"))
    bc = close.merge(oof_close[["a_id", "b_id", "baseline_logit"]], on=["a_id", "b_id"])
    bc_sc = bc.assign(credit=np.where(bc["baseline_logit"] > 0, bc["y"], 1 - bc["y"]).astype(float), inconsistent=np.nan, tie=False)
    r = summarize("feature baseline (OOF)", bc_sc, 0, 0)
    r["set"] = "close"
    rows.append(r)
    table = pd.DataFrame(rows)[["set", "row", "n_pairs", "accuracy", "acc_lo", "acc_hi", "decisive_right", "decisive_wrong", "binom_p_vs_0.5", "inconsistency_rate", "picks_first_shown_rate", "tie_rate", "parse_or_api_failure_rate", "baseline_acc_same_pairs", "diff_vs_baseline", "diff_lo", "diff_hi"]]
    table.to_csv(os.path.join(OUT, "08_main_table.csv"), index=False)
    return table, scored_clear


def added_value(clear: pd.DataFrame, scored: dict) -> pd.DataFrame:
    oof = pd.read_csv(os.path.join(OUT, "04_feature_baseline_oof_clear.csv"))
    rows = []
    for name, sc in scored.items():
        if "title-only" in name:
            continue
        d = sc.merge(oof[["a_id", "b_id", "baseline_logit"]], on=["a_id", "b_id"])
        d = d[~d["failed"]]
        y = d["y"].to_numpy()
        x0 = sm.add_constant(d[["baseline_logit"]].to_numpy())
        z = (d["diff"] / (d["diff"].std() or 1)).to_numpy()
        x1 = np.column_stack([x0, z])
        m0 = sm.Logit(y, x0).fit(disp=0)
        m1 = sm.Logit(y, x1).fit(disp=0)
        lr = 2 * (m1.llf - m0.llf)
        rows.append({
            "row": name, "n_pairs": len(d), "judge_coef_per_sd": m1.params[2], "judge_coef_se": m1.bse[2],
            "lr_stat": lr, "lr_p": chi2.sf(lr, 1),
            "auc_baseline": roc_auc_score(y, m0.predict(x0)), "auc_baseline_plus_judge": roc_auc_score(y, m1.predict(x1)),
            "auc_judge_alone": roc_auc_score(y, z) if len(np.unique(z)) > 1 else np.nan,
        })
    t = pd.DataFrame(rows)
    t["delta_auc"] = t["auc_baseline_plus_judge"] - t["auc_baseline"]
    t.to_csv(os.path.join(OUT, "08_added_value.csv"), index=False)
    return t


def post_level_residuals(eval_ids: list[str]) -> pd.Series:
    """pct_month minus an image-blind ridge prediction (trained on all other clean posts)."""
    posts = pd.read_parquet(os.path.join(ROOT, "data", "clean", "posts.parquet"))
    f = fb.post_features(posts)
    is_eval = posts["post_id"].isin(eval_ids).to_numpy()
    vec = fb.TfidfVectorizer(ngram_range=(1, 2), min_df=5, sublinear_tf=True).fit(f.loc[~is_eval, "title"])
    cols = fb.dense_cols(f)
    mean, std = f.loc[~is_eval, cols].mean(), f.loc[~is_eval, cols].std().replace(0, 1)
    x = sp.hstack([vec.transform(f["title"]), sp.csr_matrix(((f[cols] - mean) / std).to_numpy())]).tocsr()
    y = posts["pct_month"].to_numpy()
    model = RidgeCV(alphas=np.logspace(-1, 3, 5), cv=3).fit(x[~is_eval], y[~is_eval])
    resid = y[is_eval] - model.predict(x[is_eval])
    return pd.Series(resid, index=posts["post_id"][is_eval])


def pointwise(clear: pd.DataFrame) -> pd.DataFrame:
    posts = pd.read_parquet(os.path.join(ROOT, "data", "clean", "posts.parquet")).set_index("post_id")
    ids = list(dict.fromkeys(pd.concat([clear["a_id"], clear["b_id"]])))
    resid = post_level_residuals(ids)
    rows = []
    for prompt, col in (("P1", "score"), ("P2", "p2_mean")):
        for path in sorted(glob.glob(os.path.join(PARSED, f"*__{prompt}__clear*.csv"))):
            judge = os.path.basename(path).split("__")[0]
            r = pd.read_csv(path)
            r = r[r["status"] == "ok"].set_index("post_id")
            pct = posts.loc[r.index, "pct_month"]
            pairs_ = np.column_stack([r[col].to_numpy(), pct.to_numpy(), resid.loc[r.index].to_numpy()])
            rho = spearmanr(pairs_[:, 0], pairs_[:, 1])[0]
            rho_p = spearmanr(pairs_[:, 0], pairs_[:, 2])[0]
            lo, hi = boot_ci(pairs_, lambda m: spearmanr(m[:, 0], m[:, 1])[0])
            plo, phi = boot_ci(pairs_, lambda m: spearmanr(m[:, 0], m[:, 2])[0])
            rows.append({"judge": judge, "prompt": prompt, "n_images": len(r), "spearman_pct_month": rho, "lo": lo, "hi": hi,
                         "spearman_residual_pct_month": rho_p, "resid_lo": plo, "resid_hi": phi})
    t = pd.DataFrame(rows)
    t.to_csv(os.path.join(OUT, "08_pointwise.csv"), index=False)
    return t


def breakdowns(scored: dict) -> pd.DataFrame:
    rows = []
    for name, sc in scored.items():
        sc = sc.copy()
        sc["year_bin"] = pd.cut(sc["year"], [b[0] - 1 for b in YEAR_BINS] + [YEAR_BINS[-1][1]], labels=[b[2] for b in YEAR_BINS])
        for dim in ("chart_type", "year_bin"):
            for level, g in sc.groupby(dim, observed=True):
                c = g["credit"].to_numpy()
                lo, hi = boot_ci(c) if len(c) >= MIN_CELL else (np.nan, np.nan)
                rows.append({"row": name, "dimension": dim, "level": level, "n_pairs": len(g), "accuracy": c.mean(), "lo": lo, "hi": hi,
                             "note": "too few" if len(g) < MIN_CELL else ""})
    t = pd.DataFrame(rows)
    t.to_csv(os.path.join(OUT, "08_breakdowns.csv"), index=False)
    return t


def agreement(clear: pd.DataFrame, scored: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    p3 = {k: v for k, v in scored.items() if k.endswith(" P3")}
    names = sorted(p3)
    krows = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            m = p3[a][["a_id", "b_id", "AB", "BA"]].merge(p3[b][["a_id", "b_id", "AB", "BA"]], on=["a_id", "b_id"])
            post_a = np.concatenate([m["a_id"], m["a_id"]])
            xa = np.concatenate([m["AB_x"], m["BA_x"]])
            xb = np.concatenate([m["AB_y"], m["BA_y"]])
            ok = pd.notna(xa) & pd.notna(xb)
            kappa = cohen_kappa_score(xa[ok] == post_a[ok], xb[ok] == post_a[ok])
            krows.append({"judge_a": a, "judge_b": b, "n_decisions": int(ok.sum()), "cohen_kappa": kappa})
    kappa = pd.DataFrame(krows)
    kappa.to_csv(os.path.join(OUT, "08_agreement_kappa_P3.csv"), index=False)
    p1 = {}
    for path in sorted(glob.glob(os.path.join(PARSED, f"*__P1__clear{N_CLEAR}.csv"))):
        r = pd.read_csv(path)
        p1[os.path.basename(path).split("__")[0]] = r[r["status"] == "ok"].set_index("post_id")["score"]
    srows = []
    js = sorted(p1)
    for i, a in enumerate(js):
        for b in js[i + 1:]:
            idx = p1[a].index.intersection(p1[b].index)
            srows.append({"judge_a": a, "judge_b": b, "n_images": len(idx), "spearman_P1": spearmanr(p1[a][idx], p1[b][idx])[0]})
    sp1 = pd.DataFrame(srows)
    sp1.to_csv(os.path.join(OUT, "08_agreement_spearman_P1.csv"), index=False)
    return kappa, sp1


def bias_probes(clear: pd.DataFrame, scored: dict) -> pd.DataFrame:
    feats_path = os.path.join(ROOT, "data", "clean", "image_features.parquet")
    if not os.path.exists(feats_path):
        return pd.DataFrame()
    f = pd.read_parquet(feats_path).set_index("post_id")
    f["log_ocr_words"] = np.log1p(f["ocr_words"])
    f["log_aspect_ratio"] = np.log(f["aspect_ratio"])
    f["log_orig_megapixels"] = np.log(f["orig_megapixels"])
    f = f[BIAS_FEATURES]
    f = (f - f.mean()) / f.std()
    d = clear[clear["a_id"].isin(f.index) & clear["b_id"].isin(f.index)]
    x = f.loc[d["a_id"]].to_numpy() - f.loc[d["b_id"]].to_numpy()
    rows = []

    def fit(y: np.ndarray, x_: np.ndarray, target: str) -> None:
        m = sm.Logit(y, sm.add_constant(x_)).fit(disp=0)
        for i, feat in enumerate(BIAS_FEATURES):
            rows.append({"target": target, "feature": feat, "coef": m.params[i + 1], "se": m.bse[i + 1], "n_pairs": len(y)})

    fit(d["y"].to_numpy(), x, "audience")
    for name, sc in scored.items():
        if "title-only" in name:
            continue
        m = d[["a_id", "b_id"]].merge(sc[["a_id", "b_id", "judge_pick_a"]], on=["a_id", "b_id"], how="left")
        ok = m["judge_pick_a"].notna().to_numpy()
        fit(m["judge_pick_a"].to_numpy()[ok], x[ok], name)
    t = pd.DataFrame(rows)
    t.to_csv(os.path.join(OUT, "08_bias_probes.csv"), index=False)
    return t


def main() -> None:
    clear, close = load_pairs("clear", N_CLEAR), load_pairs("close", N_CLOSE)
    table, scored = main_table(clear, close)
    print(table.to_string())
    for name, sc in scored.items():
        sc.to_csv(os.path.join(OUT, f"08_scored__{name.replace(' ', '__')}.csv"), index=False)
    print(added_value(clear, scored).to_string())
    print(pointwise(clear).to_string())
    breakdowns(scored)
    k, s1 = agreement(clear, scored)
    print(k.to_string(), "\n", s1.to_string())
    print(bias_probes(clear, scored).to_string())


if __name__ == "__main__":
    main()
