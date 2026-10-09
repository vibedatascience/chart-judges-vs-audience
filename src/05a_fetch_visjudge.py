import json
import os
import urllib.parse
import urllib.request

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "data", "raw", "visjudgebench", "VisJudgeBench.json")
IMG_DIR = os.path.join(ROOT, "data", "raw", "visjudgebench")
OUT = os.path.join(ROOT, "pairs", "calibration.parquet")
SEED = 20261008
N = 150
RAW = "https://raw.githubusercontent.com/HKUSTDial/VisJudgeBench/main/"


def main() -> None:
    rows = [json.loads(line) for line in open(SRC)]
    df = pd.DataFrame(rows)
    df = df[df["type"] == "single_view"].sample(N, random_state=SEED).reset_index(drop=True)
    for path in df["image_path"]:
        dst = os.path.join(IMG_DIR, path)
        if os.path.exists(dst):
            continue
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        urllib.request.urlretrieve(RAW + urllib.parse.quote(path), dst)
    for d in ["data_fidelity", "semantic_readability", "insight_discovery", "design_style", "visual_composition", "color_harmony"]:
        df[f"gt_{d}"] = df["dimension_scores"].map(lambda s, d=d: s.get(d))
    df.drop(columns=["dimension_scores"]).to_parquet(OUT, index=False)
    print(df[["_id", "subtype", "image_path", "overall_score"]].head(), len(df))


if __name__ == "__main__":
    main()
