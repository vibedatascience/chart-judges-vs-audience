import argparse
import json
import os
import re
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
from tqdm import tqdm

from judge_client import BudgetExceeded, cost_usd, judge, total_spend
from prompts import P1, P2, P3, RETRY_SUFFIX

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(ROOT, "judges", "raw")
PARSED_DIR = os.path.join(ROOT, "judges", "parsed")
IMG_DIR = os.path.join(ROOT, "data", "images_std")

JUDGES = {
    "gpt-5": ("gpt-5", {"reasoning_effort": "minimal"}),
    "haiku-4.5": ("global.anthropic.claude-haiku-4-5-20251001-v1:0", {"temperature": 0}),
    "gemini-2.5-flash": ("gemini-2.5-flash", {"temperature": 0, "thinking_budget": 0}),
    "sonnet-5.5": ("global.anthropic.claude-sonnet-5-5", {"effort": "low"}),
}
P2_DIMS = ["data_fidelity", "semantic_readability", "insight_discovery", "design_style", "visual_composition", "color_harmony"]


def extract_json(text: str) -> dict | None:
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return None
    try:
        obj = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    return obj if isinstance(obj, dict) else None


def parse(prompt: str, text: str) -> dict | None:
    obj = extract_json(text)
    if obj is None:
        return None
    if prompt == "P1":
        s = obj.get("score")
        if isinstance(s, bool) or not isinstance(s, (int, float)) or not 1 <= s <= 10:
            return None
        return {"score": float(s), "reason": str(obj.get("reason", ""))}
    if prompt == "P2":
        vals = {}
        for d in P2_DIMS:
            v = obj.get(d)
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not 1 <= v <= 5:
                return None
            vals[d] = float(v)
        return {**vals, "p2_mean": sum(vals.values()) / len(vals)}
    if prompt == "P3":
        w, c = obj.get("winner"), obj.get("confidence")
        if w not in ("A", "B"):
            return None
        conf = float(c) if isinstance(c, (int, float)) and not isinstance(c, bool) and 1 <= c <= 5 else None
        return {"pick": w, "confidence": conf, "reason": str(obj.get("reason", ""))}
    raise ValueError(prompt)


def image(pid: str) -> bytes:
    with open(os.path.join(IMG_DIR, f"{pid}.jpg"), "rb") as f:
        return f.read()


def run_one(judge_name: str, task: dict) -> dict:
    model, settings = JUDGES[judge_name]
    prompt = task["prompt"]
    attempts = [(prompt, task["parts"]), (f"{prompt}-retry", task["parts"][:-1] + [task["parts"][-1] + RETRY_SUFFIX])]
    rec = {k: v for k, v in task.items() if k != "parts"}
    rec.update({"judge": judge_name, "model_id": model, "settings": settings, "cost_usd": 0.0})
    for attempt, (pid, parts) in enumerate(attempts):
        try:
            r = judge(model, pid, parts, settings)
        except BudgetExceeded:
            raise
        except Exception as e:
            rec.update({"status": "api_error", "error": str(e)[:300], "attempts": attempt + 1})
            return rec
        rec["cost_usd"] += 0.0 if r["cached"] else cost_usd(r)
        rec.update({"raw_text": r["text"], "finish": r["finish"], "input_tokens": r["input_tokens"], "output_tokens": r["output_tokens"], "attempts": attempt + 1})
        parsed = parse(prompt, r["text"])
        if parsed is not None:
            rec.update({"status": "ok", **parsed})
            return rec
    rec["status"] = "parse_failure"
    return rec


def build_tasks(prompt: str, set_name: str, n: int) -> list[dict]:
    pairs = pd.read_parquet(os.path.join(ROOT, "pairs", f"{set_name}.parquet")).head(n)
    if prompt in ("P1", "P2"):
        ids = list(dict.fromkeys(pd.concat([pairs["a_id"], pairs["b_id"]]).tolist()))
        text = P1 if prompt == "P1" else P2
        return [{"task_id": pid, "prompt": prompt, "post_id": pid, "parts": [image(pid), text]} for pid in ids]
    if prompt == "P3":
        tasks = []
        for _, r in pairs.iterrows():
            for order, (first, second) in (("AB", (r["a_id"], r["b_id"])), ("BA", (r["b_id"], r["a_id"]))):
                tasks.append({
                    "task_id": f"{r['a_id']}|{r['b_id']}|{order}", "prompt": "P3", "a_id": r["a_id"], "b_id": r["b_id"], "order": order,
                    "shown_first": first, "parts": ["Chart A:", image(first), "Chart B:", image(second), P3],
                })
        return tasks
    raise ValueError(prompt)


def run(judge_name: str, prompt: str, set_name: str, n: int, workers: int = 8) -> pd.DataFrame:
    tasks = build_tasks(prompt, set_name, n)
    tag = f"{judge_name}__{prompt}__{set_name}{n}"
    out_rows = []
    with ThreadPoolExecutor(workers) as ex:
        for rec in tqdm(ex.map(lambda t: run_one(judge_name, t), tasks), total=len(tasks), desc=tag):
            out_rows.append(rec)
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(PARSED_DIR, exist_ok=True)
    with open(os.path.join(RAW_DIR, f"{tag}.jsonl"), "w") as f:
        for rec in out_rows:
            f.write(json.dumps(rec, default=str) + "\n")
    df = pd.DataFrame(out_rows).drop(columns=["raw_text", "settings"], errors="ignore")
    df.to_csv(os.path.join(PARSED_DIR, f"{tag}.csv"), index=False)
    return df


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--judge", required=True, choices=sorted(JUDGES))
    ap.add_argument("--prompt", required=True, choices=["P1", "P2", "P3"])
    ap.add_argument("--set", required=True)
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    before = total_spend()
    df = run(a.judge, a.prompt, a.set, a.n, a.workers)
    print(df["status"].value_counts().to_string())
    print(f"this run ${df['cost_usd'].sum():.4f}; total spend ${before + df['cost_usd'].sum():.4f}")


if __name__ == "__main__":
    main()
