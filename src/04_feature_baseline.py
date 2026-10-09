import os

import numpy as np
import pandas as pd
import scipy.sparse as sp
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegressionCV
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS = os.path.join(ROOT, "data", "clean", "posts.parquet")
PAIRS_DIR = os.path.join(ROOT, "pairs")
OUT_DIR = os.path.join(ROOT, "analysis")
SEED = 20261008
N_FOLDS = 5
N_BOOT = 1000
HOURS = [str(h) for h in range(24)] + ["missing"]
WEEKDAYS = [str(d) for d in range(7)]


def post_features(posts: pd.DataFrame) -> pd.DataFrame:
    f = pd.DataFrame(index=posts["post_id"])
    title = posts["json_title"].fillna("").to_numpy()
    f["title"] = title
    f["title_len"] = [len(t) for t in title]
    f["has_oc"] = posts["json_title"].str.contains(r"\[\s*oc\s*\]", case=False, regex=True).to_numpy().astype(float)
    hour = np.where(posts["has_time"], posts["created"].dt.hour.astype(str), "missing")
    for h in HOURS:
        f[f"hour_{h}"] = (hour == h).astype(float)
    weekday = posts["created"].dt.weekday.astype(str).to_numpy()
    for d in WEEKDAYS:
        f[f"weekday_{d}"] = (weekday == d).astype(float)
    f["year"] = posts["created"].dt.year.to_numpy().astype(float)
    for c in sorted(posts["chart_type"].dropna().unique()):
        f[f"type_{c}"] = (posts["chart_type"] == c).to_numpy().astype(float)
    return f


def dense_cols(f: pd.DataFrame) -> list[str]:
    return [c for c in f.columns if c != "title"]


def pair_matrix(pairs: pd.DataFrame, f: pd.DataFrame, vec: TfidfVectorizer, mean: pd.Series, std: pd.Series) -> sp.csr_matrix:
    cols = dense_cols(f)
    a, b = f.loc[pairs["a_id"]], f.loc[pairs["b_id"]]
    dense = ((a[cols].to_numpy() - mean.to_numpy()) / std.to_numpy()) - ((b[cols].to_numpy() - mean.to_numpy()) / std.to_numpy())
    text = vec.transform(a["title"]) - vec.transform(b["title"])
    return sp.hstack([text, sp.csr_matrix(dense)]).tocsr()


def fit_predict(train: pd.DataFrame, test: pd.DataFrame, f: pd.DataFrame) -> np.ndarray:
    ids = pd.concat([train["a_id"], train["b_id"]]).unique()
    vec = TfidfVectorizer(ngram_range=(1, 2), min_df=5, sublinear_tf=True).fit(f.loc[ids, "title"])
    cols = dense_cols(f)
    mean, std = f.loc[ids, cols].mean(), f.loc[ids, cols].std().replace(0, 1)
    x = pair_matrix(train, f, vec, mean, std)
    y = (train["winner"] == "A").to_numpy().astype(int)
    x_aug, y_aug = sp.vstack([x, -x]), np.concatenate([y, 1 - y])
    model = LogisticRegressionCV(Cs=10, cv=5, l1_ratios=(0,), fit_intercept=False, scoring="neg_log_loss", max_iter=5000, random_state=SEED)
    model.fit(x_aug, y_aug)
    return model.decision_function(pair_matrix(test, f, vec, mean, std))


def oof_logits(pairs: pd.DataFrame, f: pd.DataFrame, months: pd.Series) -> np.ndarray:
    groups = pairs["a_id"].map(months).to_numpy()
    logits = np.zeros(len(pairs))
    for tr, te in GroupKFold(n_splits=N_FOLDS, shuffle=True, random_state=SEED).split(pairs, groups=groups):
        logits[te] = fit_predict(pairs.iloc[tr], pairs.iloc[te], f)
    return logits


def bootstrap_ci(y: np.ndarray, logit: np.ndarray, rng: np.random.Generator) -> dict:
    acc = lambda yy, ll: float(((ll > 0).astype(int) == yy).mean())
    accs, aucs = [], []
    n = len(y)
    for _ in range(N_BOOT):
        idx = rng.integers(0, n, n)
        accs.append(acc(y[idx], logit[idx]))
        aucs.append(roc_auc_score(y[idx], logit[idx]))
    return {
        "n": n,
        "accuracy": acc(y, logit), "acc_lo": float(np.percentile(accs, 2.5)), "acc_hi": float(np.percentile(accs, 97.5)),
        "auc": float(roc_auc_score(y, logit)), "auc_lo": float(np.percentile(aucs, 2.5)), "auc_hi": float(np.percentile(aucs, 97.5)),
    }


def main() -> None:
    rng = np.random.default_rng(SEED)
    posts = pd.read_parquet(POSTS)
    f = post_features(posts)
    months = pd.Series(posts["month"].to_numpy(), index=posts["post_id"])
    rows = []
    for name in ("clear", "close"):
        pairs = pd.read_parquet(os.path.join(PAIRS_DIR, f"{name}.parquet"))
        logit = oof_logits(pairs, f, months)
        out = pairs[["a_id", "b_id", "winner"]].copy()
        out["baseline_logit"] = logit
        out.to_csv(os.path.join(OUT_DIR, f"04_feature_baseline_oof_{name}.csv"), index=False)
        y = (pairs["winner"] == "A").to_numpy().astype(int)
        rows.append({"set": name, "model": "feature baseline (L2 logistic, month-grouped 5-fold OOF)", **bootstrap_ci(y, logit, rng)})
    table = pd.DataFrame(rows)
    table.to_csv(os.path.join(OUT_DIR, "04_feature_baseline.csv"), index=False)
    print(table.to_string())


if __name__ == "__main__":
    main()
