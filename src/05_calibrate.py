import io
import os
import sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd
from PIL import Image
from scipy.stats import pearsonr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from judge_client import total_spend  # noqa: E402
from prompts import P1, P2  # noqa: E402

run_judges = __import__("06_run_judges")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAL = os.path.join(ROOT, "pairs", "calibration.parquet")
IMG_DIR = os.path.join(ROOT, "data", "raw", "visjudgebench")
OUT_CSV = os.path.join(ROOT, "analysis", "05_calibration.csv")
OUT_MD = os.path.join(ROOT, "analysis", "05_calibration.md")
SEED = 20261008
N_BOOT = 1000
PUBLISHED = {"gpt-5": ("GPT-5", 0.428, 0.553), "gemini-2.5-flash": ("Gemini-2.0-Flash / Gemini-2.5-Pro", None, None), "haiku-4.5": ("Claude-4-Sonnet", None, None)}
PUBLISHED_CONTEXT = "Published (VisJudge-Bench v3, 648-item test set, all three types): GPT-5 r=0.428 MAE=0.553; Claude-4-Sonnet r=0.465 MAE=0.622; Gemini-2.5-Pro r=0.265 MAE=0.662; Gemini-2.0-Flash r=0.395 MAE=0.682."


def standardize(path: str) -> bytes:
    with Image.open(path) as im:
        rgba = im.convert("RGBA")
    out = Image.new("RGB", rgba.size, "white")
    out.paste(rgba, mask=rgba.getchannel("A"))
    scale = 1536 / max(out.size)
    if scale < 1:
        out = out.resize((round(out.width * scale), round(out.height * scale)), Image.LANCZOS)
    buf = io.BytesIO()
    out.save(buf, "JPEG", quality=90)
    return buf.getvalue()


def p1_on_calibration() -> pd.DataFrame:
    """P1 holistic score on the calibration items, so expert and audience agreement share one prompt and metric."""
    from scipy.stats import spearmanr

    cal = pd.read_parquet(CAL)
    images = {r["_id"]: standardize(os.path.join(IMG_DIR, r["image_path"])) for _, r in cal.iterrows()}
    rows = []
    for judge_name in ("gemini-2.5-flash", "gpt-5", "haiku-4.5"):
        tasks = [{"task_id": str(i), "prompt": "P1", "vj_id": i, "parts": [images[i], P1]} for i in cal["_id"]]
        with ThreadPoolExecutor(8) as ex:
            recs = list(ex.map(lambda t: run_judges.run_one(judge_name, t), tasks))
        df = pd.DataFrame(recs).merge(cal[["_id", "overall_score"]], left_on="vj_id", right_on="_id")
        df.drop(columns=["settings"], errors="ignore").to_csv(os.path.join(ROOT, "judges", "parsed", f"{judge_name}__P1__calibration150.csv"), index=False)
        ok = df[df["status"] == "ok"]
        rows.append({"judge": judge_name, "n_ok": len(ok), "spearman_P1_vs_expert": spearmanr(ok["score"], ok["overall_score"])[0], "pearson_P1_vs_expert": pearsonr(ok["score"], ok["overall_score"])[0]})
    t = pd.DataFrame(rows)
    t.to_csv(os.path.join(ROOT, "analysis", "05_calibration_P1.csv"), index=False)
    return t


def main() -> None:
    cal = pd.read_parquet(CAL)
    images = {r["_id"]: standardize(os.path.join(IMG_DIR, r["image_path"])) for _, r in cal.iterrows()}
    rng = np.random.default_rng(SEED)
    rows = []
    for judge_name in sorted(run_judges.JUDGES):
        tasks = [{"task_id": str(i), "prompt": "P2", "vj_id": i, "parts": [images[i], P2]} for i in cal["_id"]]
        with ThreadPoolExecutor(8) as ex:
            recs = list(ex.map(lambda t: run_judges.run_one(judge_name, t), tasks))
        df = pd.DataFrame(recs).merge(cal[["_id", "overall_score"]], left_on="vj_id", right_on="_id")
        df.drop(columns=["settings"], errors="ignore").to_csv(os.path.join(ROOT, "judges", "parsed", f"{judge_name}__P2__calibration150.csv"), index=False)
        ok = df[df["status"] == "ok"]
        y, x = ok["overall_score"].to_numpy(), ok["p2_mean"].to_numpy()
        boots = []
        for _ in range(N_BOOT):
            idx = rng.integers(0, len(ok), len(ok))
            boots.append(pearsonr(x[idx], y[idx])[0])
        name, pub_r, pub_mae = PUBLISHED[judge_name]
        r = pearsonr(x, y)[0]
        rows.append({
            "judge": judge_name, "model_id": run_judges.JUDGES[judge_name][0], "n_ok": len(ok), "n_fail": int((df["status"] != "ok").sum()),
            "pearson_r": r, "r_lo": np.percentile(boots, 2.5), "r_hi": np.percentile(boots, 97.5), "mae": float(np.abs(x - y).mean()),
            "published_model": name, "published_r": pub_r, "published_mae": pub_mae,
            "abs_diff_r": abs(r - pub_r) if pub_r is not None else None, "cost_usd": df["cost_usd"].sum(),
        })
    table = pd.DataFrame(rows)
    table.to_csv(OUT_CSV, index=False)
    lines = ["# 05 Calibration on VisJudge-Bench", "",
             f"150 `single_view` items sampled with seed {SEED} (`pairs/calibration.parquet`). Prompt P2; judge score = mean of the six dimensions; target = `overall_score`. Images standardized the same way as beautiVis (white background, long side <= 1536, JPEG q90). 95% CI from 1,000 bootstrap resamples.", "",
             PUBLISHED_CONTEXT, "",
             table.to_markdown(index=False, floatfmt=".3f"), "", f"Total spend after calibration: ${total_spend():.2f}", ""]
    open(OUT_MD, "w").write("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "p1":
        print(p1_on_calibration().to_string())
    else:
        main()
