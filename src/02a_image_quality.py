import glob
import os
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_DIR = os.path.join(ROOT, "data", "vis_images")
OUT = os.path.join(ROOT, "data", "clean", "image_quality.parquet")

Image.MAX_IMAGE_PIXELS = None


def measure(path: str) -> dict:
    with Image.open(path) as im:
        n_frames = getattr(im, "n_frames", 1)
        mode = im.mode
        rgba = im.convert("RGBA")
        rgba.thumbnail((256, 256))
        a = np.asarray(rgba).astype(np.float32)
    alpha = a[..., 3] / 255.0
    on_black = a[..., :3] * alpha[..., None]
    on_white = on_black + 255.0 * (1 - alpha[..., None])
    gray = on_white.mean(axis=2)
    return {
        "pp_image_file": os.path.basename(path),
        "mode": mode,
        "n_frames": n_frames,
        "frac_transparent": float((alpha < 0.5).mean()),
        "gray_std": float(gray.std()),
        "gray_mean": float(gray.mean()),
        "black_mean_if_flattened": float(on_black.mean()),
    }


def main() -> None:
    paths = sorted(glob.glob(os.path.join(IMG_DIR, "*", "*")))
    with ProcessPoolExecutor() as ex:
        rows = list(ex.map(measure, paths, chunksize=64))
    pd.DataFrame(rows).to_parquet(OUT, index=False)


if __name__ == "__main__":
    main()
