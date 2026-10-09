import os

import easyocr
import pandas as pd
from rapidfuzz import fuzz

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "analysis")
RECALL_THRESHOLD = 80
CONTAMINATION_FLAG = 0.05


def main() -> None:
    pr = pd.read_csv(os.path.join(OUT, "07_recognition_probe.csv"))
    reader = easyocr.Reader(["en"], gpu=False, verbose=False)
    ocr = {pid: " ".join(reader.readtext(os.path.join(ROOT, "data", "images_std", f"{pid}.jpg"), detail=0)) for pid in pr["post_id"].unique()}
    pr["ocr_text"] = pr["post_id"].map(ocr)
    pr["guess_vs_ocr"] = [fuzz.partial_token_set_ratio(str(g or ""), o) if g else 0 for g, o in zip(pr["guess_title"], pr["ocr_text"])]
    pr["true_title_in_image"] = [fuzz.partial_token_set_ratio(t, o) >= RECALL_THRESHOLD for t, o in zip(pr["true_title"], pr["ocr_text"])]
    pr["recall_not_in_image"] = pr["recall"] & (pr["guess_vs_ocr"] < RECALL_THRESHOLD)
    pr.to_csv(os.path.join(OUT, "07_recognition_probe.csv"), index=False)
    summ = pr.groupby("judge").agg(
        n=("post_id", "size"), claimed_seen=("seen", lambda s: (s == True).mean()),  # noqa: E712
        recall_rate=("recall", "mean"), recall_not_in_image_rate=("recall_not_in_image", "mean"),
        true_title_readable_in_image=("true_title_in_image", "mean"),
    ).reset_index()
    summ["flag_contaminated"] = summ["recall_not_in_image_rate"] > CONTAMINATION_FLAG
    summ.to_csv(os.path.join(OUT, "07_recognition_summary.csv"), index=False)
    print(summ.to_string())
    print(pr[pr["recall"]][["judge", "post_id", "guess_vs_ocr", "recall_not_in_image", "guess_title"]].to_string())


if __name__ == "__main__":
    main()
