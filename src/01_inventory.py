import glob
import os

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_DIR = os.path.join(ROOT, "data", "vis_csv", "vis_csv")
IMG_DIR = os.path.join(ROOT, "data", "vis_images")
OUT = os.path.join(ROOT, "analysis", "01_inventory.md")
EXPECTED = [
    "json_title", "json_author", "json_created_date", "json_url", "json_full_permalink",
    "json_score", "json_ups", "json_downs", "json_num_comments", "pp_sanitized_title",
    "pp_image_file", "gpt_chart_type", "gpt_high_level_categories", "gpt_cleaned_chart_type",
    "gpt_overarching_chart_type",
]


def load() -> pd.DataFrame:
    frames = []
    for path in sorted(glob.glob(os.path.join(CSV_DIR, "*.csv"))):
        df = pd.read_csv(path, dtype=str, keep_default_na=False)
        df["source_csv"] = os.path.basename(path)
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def image_files() -> set[str]:
    if not os.path.isdir(IMG_DIR):
        return set()
    return {os.path.basename(p) for p in glob.glob(os.path.join(IMG_DIR, "**", "*"), recursive=True)}


def md(df: pd.DataFrame) -> str:
    return df.to_markdown(index=False)


def main() -> None:
    df = load()
    missing_cols = [c for c in EXPECTED if c not in df.columns]
    df["score"] = pd.to_numeric(df["json_score"], errors="coerce")
    df["created"] = pd.to_datetime(df["json_created_date"], errors="coerce", format="mixed")
    df["has_time"] = df["json_created_date"].str.len() > 10
    df["year"] = df["created"].dt.year
    imgs = image_files()
    n_found = df["pp_image_file"].isin(imgs).sum()

    otype = df["gpt_overarching_chart_type"].str.strip()
    multi = otype.str.contains(",")

    lines = ["# 01 Inventory", "", f"Source: beautiVis/beautiVis @ 739821c9703a6fa23f64895931b1ccc3a9238f2b, vis_csv.zip ({df['source_csv'].nunique()} monthly CSVs)", ""]
    lines += ["## Counts", ""]
    lines.append(md(pd.DataFrame({
        "metric": [
            "rows", "unique pp_image_file", "image files found on disk", "rows with image missing",
            "rows missing score", "rows missing/unparseable created date", "missing expected columns",
            "rows with multi-valued gpt_overarching_chart_type",
            "rows with date but no time-of-day",
            "rows with score < 5",
        ],
        "value": [
            len(df), df["pp_image_file"].nunique(), int(n_found), int(len(df) - n_found),
            int(df["score"].isna().sum()), int(df["created"].isna().sum()), ", ".join(missing_cols) or "none",
            int(multi.sum()),
            int((~df["has_time"]).sum()),
            int((df["score"] < 5).sum()),
        ],
    })))
    lines += ["", "## Posts per year", ""]
    per_year = df.groupby("year").agg(posts=("score", "size"), no_time=("has_time", lambda s: int((~s).sum())), median=("score", "median"), p90=("score", lambda s: s.quantile(0.9))).reset_index()
    per_year["year"] = per_year["year"].astype("Int64")
    lines.append(md(per_year))
    lines += ["", "## Posts per gpt_overarching_chart_type (raw string, top 30)", ""]
    vc = otype.replace("", "(empty)").value_counts()
    lines.append(md(vc.head(30).rename_axis("type").reset_index(name="posts")))
    lines.append(f"\n{len(vc)} distinct raw values in total.")
    lines += ["", "## Posts per primary type (first listed category)", ""]
    primary = otype.str.split(",").str[0].str.strip().replace("", "(empty)")
    lines.append(md(primary.value_counts().rename_axis("primary_type").reset_index(name="posts")))
    lines += ["", "## Score quantiles", ""]
    qs = [0, 0.1, 0.25, 0.5, 0.75, 0.9, 0.99, 1.0]
    lines.append(md(pd.DataFrame({"quantile": qs, "score": [df["score"].quantile(q) for q in qs]})))
    lines += ["", "## 10 sample rows (seed 20261008)", ""]
    sample = df.sample(10, random_state=20261008)[
        ["pp_image_file", "json_created_date", "json_score", "json_num_comments", "gpt_overarching_chart_type", "json_title"]
    ].copy()
    sample["json_title"] = sample["json_title"].str.slice(0, 80)
    lines.append(md(sample))
    lines.append("")
    with open(OUT, "w") as f:
        f.write("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
