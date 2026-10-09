import glob
import os
from concurrent.futures import ProcessPoolExecutor

import imagehash
from rapidfuzz import fuzz
import numpy as np
import pandas as pd
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_DIR = os.path.join(ROOT, "data", "vis_csv", "vis_csv")
IMG_DIR = os.path.join(ROOT, "data", "vis_images")
STD_DIR = os.path.join(ROOT, "data", "images_std")
OUT_PARQUET = os.path.join(ROOT, "data", "clean", "posts.parquet")
IMG_META = os.path.join(ROOT, "data", "clean", "image_meta.parquet")
OUT_MD = os.path.join(ROOT, "analysis", "02_clean.md")
MIN_SHORT_SIDE = 300
MIN_SCORE = 5
PHASH_MAX_DIST = 2
MIN_GRAY_STD = 2.0
PLACEHOLDER_MIN_GROUP = 3
PLACEHOLDER_MAX_TITLE_SIM = 60
QUALITY = os.path.join(ROOT, "data", "clean", "image_quality.parquet")
STD_LONG_SIDE = 1536
DROP_TYPES = {"", "none", "None", "Other"}

Image.MAX_IMAGE_PIXELS = None


def index_images() -> dict[str, str]:
    return {os.path.basename(p): p for p in glob.glob(os.path.join(IMG_DIR, "**", "*.*"), recursive=True)}


def inspect(path: str) -> dict:
    try:
        with Image.open(path) as im:
            im.load()
            w, h = im.size
            ph = str(imagehash.phash(im.convert("RGB")))
        return {"width": w, "height": h, "phash": ph, "readable": True}
    except Exception as e:
        return {"width": None, "height": None, "phash": None, "readable": False, "error": repr(e)[:200]}


def standardize(args: tuple[str, str]) -> str:
    src, dst = args
    if os.path.exists(dst):
        return dst
    with Image.open(src) as im:
        rgba = im.convert("RGBA")
        im = Image.new("RGB", rgba.size, "white")
        im.paste(rgba, mask=rgba.getchannel("A"))
        scale = STD_LONG_SIDE / max(im.size)
        if scale < 1:
            im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
        im.save(dst, "JPEG", quality=90)
    return dst


def load_csv() -> pd.DataFrame:
    df = pd.concat(
        [pd.read_csv(p, dtype=str, keep_default_na=False) for p in sorted(glob.glob(os.path.join(CSV_DIR, "*.csv")))],
        ignore_index=True,
    )
    df["score"] = pd.to_numeric(df["json_score"], errors="coerce")
    df["num_comments"] = pd.to_numeric(df["json_num_comments"], errors="coerce")
    df["created"] = pd.to_datetime(df["json_created_date"], errors="coerce", format="mixed")
    df["has_time"] = df["json_created_date"].str.len() > 10
    df["chart_type_raw"] = df["gpt_overarching_chart_type"].str.strip()
    df["post_id"] = df["pp_image_file"].str.rsplit(".", n=1).str[0]
    return df


def image_meta(df: pd.DataFrame, paths: dict[str, str]) -> pd.DataFrame:
    if os.path.exists(IMG_META):
        meta = pd.read_parquet(IMG_META)
        if set(meta["pp_image_file"]) >= set(df["pp_image_file"]):
            return meta
    files = [f for f in df["pp_image_file"] if f in paths]
    with ProcessPoolExecutor() as ex:
        rows = list(ex.map(inspect, [paths[f] for f in files], chunksize=64))
    meta = pd.DataFrame(rows)
    meta.insert(0, "pp_image_file", files)
    meta.to_parquet(IMG_META, index=False)
    return meta


def dedup_groups(df: pd.DataFrame) -> pd.Series:
    """Union-find over pHash pairs within Hamming distance; returns the earliest post_id per group."""
    hashes = np.array([int(h, 16) for h in df["phash"]], dtype=np.uint64)
    n = len(hashes)
    parent = np.arange(n)

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    block = 512
    for start in range(0, n, block):
        dist = np.bitwise_count(hashes[start:start + block, None] ^ hashes[None, :])
        ii, jj = np.nonzero(dist <= PHASH_MAX_DIST)
        for i, j in zip(ii + start, jj):
            if i < j:
                ri, rj = find(i), find(j)
                if ri != rj:
                    parent[max(ri, rj)] = min(ri, rj)
    roots = np.array([find(i) for i in range(n)])
    return pd.Series(roots, index=df.index)


def title_similarity(titles: list[str]) -> float:
    sims = [fuzz.token_set_ratio(a, b) for i, a in enumerate(titles) for b in titles[i + 1:]]
    return float(np.median(sims))


def main() -> None:
    df = load_csv()
    paths = index_images()
    n_no_file = int((~df["pp_image_file"].isin(paths)).sum())
    steps = [("raw rows", len(df))]

    meta = image_meta(df, paths)
    df = df.merge(meta, on="pp_image_file", how="left")
    df["readable"] = df["readable"].astype("boolean").fillna(False).astype(bool)

    quality = pd.read_parquet(QUALITY)[["pp_image_file", "gray_std"]]
    df = df.merge(quality, on="pp_image_file", how="left")
    df = df[df["readable"] & df["score"].notna() & df["created"].notna()]
    steps.append(("1a. missing/unreadable image, missing score or date", len(df)))
    df = df[df["gray_std"] >= MIN_GRAY_STD]
    steps.append((f"1b. blank image (grayscale std < {MIN_GRAY_STD})", len(df)))
    df = df[~df["chart_type_raw"].isin(DROP_TYPES)]
    steps.append(("2. chart type empty / none / Other", len(df)))
    df = df[df[["width", "height"]].min(axis=1) >= MIN_SHORT_SIDE]
    steps.append((f"3. short side < {MIN_SHORT_SIDE}px", len(df)))
    df = df[df["score"] >= MIN_SCORE]
    steps.append((f"4. score < {MIN_SCORE}", len(df)))

    df = df.sort_values(["created", "post_id"]).reset_index(drop=True)
    roots = dedup_groups(df)
    df["dup_group"] = df["post_id"].values[roots.values]
    sizes = df["dup_group"].map(df["dup_group"].value_counts())
    n_groups_multi = int((df["dup_group"].value_counts() > 1).sum())
    placeholder = {
        g for g, grp in df[sizes >= PLACEHOLDER_MIN_GROUP].groupby("dup_group")
        if title_similarity(grp["json_title"].tolist()) < PLACEHOLDER_MAX_TITLE_SIM
    }
    is_placeholder = df["dup_group"].isin(placeholder)
    n_placeholder_posts = int(is_placeholder.sum())
    df = df[~is_placeholder.values & (roots.values == np.arange(len(df)))].reset_index(drop=True)
    steps.append((
        f"5. near-duplicate (pHash Hamming <= {PHASH_MAX_DIST}): keep earliest; drop whole group if "
        f">= {PLACEHOLDER_MIN_GROUP} posts with median title similarity < {PLACEHOLDER_MAX_TITLE_SIM}",
        len(df),
    ))

    os.makedirs(STD_DIR, exist_ok=True)
    jobs = [(paths[f], os.path.join(STD_DIR, f"{pid}.jpg")) for f, pid in zip(df["pp_image_file"], df["post_id"])]
    with ProcessPoolExecutor() as ex:
        df["image_std"] = [os.path.relpath(p, ROOT) for p in ex.map(standardize, jobs, chunksize=32)]

    df["multi_type"] = df["chart_type_raw"].str.contains(",")
    df["chart_type"] = df["chart_type_raw"].where(~df["multi_type"])
    keep = [
        "post_id", "pp_image_file", "image_std", "json_title", "pp_sanitized_title", "json_author", "json_full_permalink",
        "json_url", "created", "has_time", "score", "num_comments", "chart_type_raw", "chart_type", "multi_type",
        "gpt_cleaned_chart_type", "gpt_high_level_categories", "width", "height", "gray_std", "phash", "dup_group",
    ]
    df[keep].to_parquet(OUT_PARQUET, index=False)

    table = pd.DataFrame(steps, columns=["step", "rows_remaining"])
    table["removed"] = (-table["rows_remaining"].diff()).fillna(0).astype(int)
    unreadable = int((~meta["readable"]).sum())
    lines = [
        "# 02 Clean", "", table.to_markdown(index=False), "",
        f"- CSV rows whose image file was not found in the zips: {n_no_file}",
        f"- Image files that failed to open: {unreadable}",
        f"- Duplicate groups with more than one post: {n_groups_multi}",
        f"- Placeholder/template groups dropped entirely: {len(placeholder)} groups, {n_placeholder_posts} posts",
        f"- Multi-valued chart type rows kept in posts.parquet (excluded from pairing): {int(df['multi_type'].sum())}",
        f"- Single-type rows available for pairing: {int((~df['multi_type']).sum())}",
        f"- Rows with no time of day: {int((~df['has_time']).sum())}",
        "", "## Chart type (single-type rows)", "",
        df["chart_type"].value_counts().rename_axis("chart_type").reset_index(name="posts").to_markdown(index=False),
        "", "## Year", "",
        df["created"].dt.year.value_counts().sort_index().rename_axis("year").reset_index(name="posts").to_markdown(index=False),
        "",
    ]
    with open(OUT_MD, "w") as f:
        f.write("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
