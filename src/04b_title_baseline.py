import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from judge_client import BudgetExceeded, cost_usd, judge, total_spend  # noqa: E402
from prompts import RETRY_SUFFIX, TITLE_ONLY  # noqa: E402

run_judges = __import__("06_run_judges")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JUDGE = "gpt-5"
N_PAIRS = 500
SEED = 20261008
N_BOOT = 1000
RETRY_TEXT = "\nAnswer with the single letter A or B only."


def parse_letter(text: str) -> str | None:
    found = re.findall(r"\b([AB])\b", text.strip())
    return found[0] if len(set(found)) == 1 else None


def run_one(task: dict) -> dict:
    model, settings = run_judges.JUDGES[JUDGE]
    rec = {k: v for k, v in task.items() if k != "text"}
    rec["cost_usd"] = 0.0
    for attempt, (pid, text) in enumerate([("title-only", task["text"]), ("title-only-retry", task["text"] + RETRY_TEXT)]):
        try:
            r = judge(model, pid, [text], settings)
        except BudgetExceeded:
            raise
        except Exception as e:
            rec.update({"status": "api_error", "error": str(e)[:300]})
            return rec
        rec["cost_usd"] += 0.0 if r["cached"] else cost_usd(r)
        rec["raw_text"] = r["text"]
        pick = parse_letter(r["text"])
        if pick:
            rec.update({"status": "ok", "pick": pick, "attempts": attempt + 1})
            return rec
    rec["status"] = "parse_failure"
    return rec


def main() -> None:
    posts = pd.read_parquet(os.path.join(ROOT, "data", "clean", "posts.parquet")).set_index("post_id")
    pairs = pd.read_parquet(os.path.join(ROOT, "pairs", "clear.parquet")).head(N_PAIRS)
    tasks = []
    for _, r in pairs.iterrows():
        for order, (first, second) in (("AB", (r["a_id"], r["b_id"])), ("BA", (r["b_id"], r["a_id"]))):
            text = TITLE_ONLY.format(title_a=posts.at[first, "json_title"], title_b=posts.at[second, "json_title"])
            tasks.append({"a_id": r["a_id"], "b_id": r["b_id"], "winner": r["winner"], "order": order, "shown_first": first, "text": text})
    with ThreadPoolExecutor(8) as ex:
        recs = pd.DataFrame(list(ex.map(run_one, tasks)))
    recs.to_csv(os.path.join(ROOT, "judges", "parsed", f"{JUDGE}__title-only__clear{N_PAIRS}.csv"), index=False)
    print(recs["status"].value_counts().to_string(), f"\ncost ${recs['cost_usd'].sum():.4f}; total ${total_spend():.4f}")


if __name__ == "__main__":
    main()
