import os

import cv2
import easyocr
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from tqdm import tqdm

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_DIR = os.path.join(ROOT, "data", "images_std")
OUT = os.path.join(ROOT, "data", "clean", "image_features.parquet")
SEED = 20261008
SETS = [("clear", 2000)]
MAX_K = 12
MIN_CLUSTER_SHARE = 0.02
COLOR_SAMPLE_SIDE = 96


def dominant_colors(img_bgr: np.ndarray) -> int:
    small = cv2.resize(img_bgr, (COLOR_SAMPLE_SIDE, COLOR_SAMPLE_SIDE), interpolation=cv2.INTER_AREA)
    lab = cv2.cvtColor(small, cv2.COLOR_BGR2LAB).reshape(-1, 3).astype(np.float32)
    k = min(MAX_K, len(np.unique(lab, axis=0)))
    labels = KMeans(n_clusters=k, n_init=3, random_state=SEED).fit_predict(lab)
    shares = np.bincount(labels) / len(labels)
    return int((shares >= MIN_CLUSTER_SHARE).sum())


def main() -> None:
    posts = pd.read_parquet(os.path.join(ROOT, "data", "clean", "posts.parquet")).set_index("post_id")
    ids = []
    for name, n in SETS:
        p = pd.read_parquet(os.path.join(ROOT, "pairs", f"{name}.parquet")).head(n)
        ids += pd.concat([p["a_id"], p["b_id"]]).tolist()
    ids = list(dict.fromkeys(ids))
    done = pd.read_parquet(OUT) if os.path.exists(OUT) else pd.DataFrame(columns=["post_id"])
    todo = [i for i in ids if i not in set(done["post_id"])]
    reader = easyocr.Reader(["en"], gpu=False, verbose=False)
    rows = []
    for pid in tqdm(todo):
        img = cv2.imread(os.path.join(IMG_DIR, f"{pid}.jpg"))
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        words = sum(len(t.split()) for t in reader.readtext(img, detail=0))
        edges = cv2.Canny(gray, 100, 200)
        rows.append({
            "post_id": pid,
            "ocr_words": words,
            "n_colors": dominant_colors(img),
            "edge_density": float((edges > 0).mean()),
            "aspect_ratio": img.shape[1] / img.shape[0],
            "orig_megapixels": posts.at[pid, "width"] * posts.at[pid, "height"] / 1e6,
        })
        if len(rows) % 100 == 0:
            done = pd.concat([done, pd.DataFrame(rows)], ignore_index=True)
            done.to_parquet(OUT, index=False)
            rows = []
    pd.concat([done, pd.DataFrame(rows)], ignore_index=True).to_parquet(OUT, index=False)


if __name__ == "__main__":
    main()
