import json
import os
import re
import sys
import textwrap

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from judge_client import judge, total_spend  # noqa: E402

run_judges = __import__("06_run_judges")
analysis = __import__("08_analysis")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "figures", "gallery")
BEST = ("gpt-5", "P3", "clear250")
CODER = "haiku-4.5"
N_SHOW = 20
MIN_CONF = 4
TILE = 520
CODES = [
    "topic appeal", "novelty or humor", "map or geographic", "polish over substance", "readability problem the judge missed",
    "data density", "misleading or questionable encoding", "other",
]
CODER_PROMPT = """Two charts were posted to r/dataisbeautiful in the same week. The audience strongly preferred the one marked AUDIENCE WINNER, but an AI judge preferred the other.
Chart 1 (AUDIENCE WINNER) title: {win_title}
Chart 2 (AI judge's pick) title: {lose_title}
AI judge's reason: {reason}
Pick the single best explanation for the disagreement from this list: {codes}.
Respond with JSON only: {{"code": "<one code from the list>", "note": "<one sentence>"}}"""


def font(size: int) -> ImageFont.ImageFont:
    for path in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/dejavu/DejaVuSans.ttf"):
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def tile(pid: str, label: str, posts: pd.DataFrame) -> Image.Image:
    im = Image.open(os.path.join(ROOT, "data", "images_std", f"{pid}.jpg")).convert("RGB")
    im.thumbnail((TILE, TILE))
    canvas = Image.new("RGB", (TILE, TILE + 120), "white")
    canvas.paste(im, ((TILE - im.width) // 2, 0))
    p = posts.loc[pid]
    d = ImageDraw.Draw(canvas)
    text = f"{label}\nscore {int(p['score'])} | month pct {p['pct_month']:.2f} | {p['chart_type']} | {pid}\n" + "\n".join(textwrap.wrap(p["json_title"], 80)[:3])
    d.multiline_text((6, TILE + 6), text, fill="black", font=font(13), spacing=3)
    return canvas


def sheet(rows: pd.DataFrame, posts: pd.DataFrame, name: str) -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    w, h = 2 * TILE + 30, TILE + 120 + 70
    for i, (_, r) in enumerate(rows.iterrows()):
        canvas = Image.new("RGB", (w, h), "white")
        tag = lambda pid: "Chart A" if pid == r["a_id"] else "Chart B"  # noqa: E731
        canvas.paste(tile(r["winner_id"], f"AUDIENCE WINNER (shown as {tag(r['winner_id'])} in the AB order)", posts), (0, 0))
        canvas.paste(tile(r["loser_id"], f"audience loser (shown as {tag(r['loser_id'])} in the AB order)", posts), (TILE + 30, 0))
        d = ImageDraw.Draw(canvas)
        reason = "\n".join(textwrap.wrap(f"Judge ({BEST[0]} {BEST[1]}, mean confidence {r['conf']:.1f}, AB-order reason) picked the {'winner' if r['credit'] == 1 else 'loser'}: {r['reason']}", 150)[:2])
        d.multiline_text((6, TILE + 128), reason, fill="#E60023", font=font(13))
        canvas.save(os.path.join(OUT_DIR, f"{name}_{i + 1:02d}.jpg"), quality=88)


def main() -> None:
    posts = pd.read_parquet(os.path.join(ROOT, "data", "clean", "posts.parquet")).set_index("post_id")
    clear = analysis.load_pairs("clear", 250)
    recs = analysis.parsed(*BEST)
    sc = analysis.score_pairwise(clear, recs)
    reasons = recs[recs["order"] == "AB"].set_index(["a_id", "b_id"])["reason"]
    sc["reason"] = [reasons.get((a, b), "") for a, b in zip(sc["a_id"], sc["b_id"])]
    sc["conf"] = sc[["conf_AB", "conf_BA"]].mean(axis=1)
    sc["loser_id"] = np.where(sc["winner_id"] == sc["a_id"], sc["b_id"], sc["a_id"])
    wrong = sc[(sc["credit"] == 0) & (sc["conf"] >= MIN_CONF)].sort_values("conf", ascending=False).head(N_SHOW)
    right = sc[sc["credit"] == 1].sort_values("conf", ascending=False).head(N_SHOW)
    sheet(wrong, posts, "wrong")
    sheet(right, posts, "right")
    model, settings = run_judges.JUDGES[CODER]
    coded = []
    for _, r in wrong.iterrows():
        text = CODER_PROMPT.format(win_title=posts.at[r["winner_id"], "json_title"], lose_title=posts.at[r["loser_id"], "json_title"], reason=r["reason"], codes="; ".join(CODES))
        out = judge(model, "gallery-coder", [run_judges.image(r["winner_id"]), run_judges.image(r["loser_id"]), text], settings)
        m = re.search(r"\{.*\}", out["text"], re.S)
        try:
            obj = json.loads(m.group(0)) if m else {}
        except json.JSONDecodeError:
            obj = {}
        coded.append({"winner_id": r["winner_id"], "loser_id": r["loser_id"], "judge_conf": r["conf"], "judge_reason": r["reason"],
                      "draft_code": obj.get("code", "PARSE_FAILURE"), "draft_note": obj.get("note", ""), "status": "DRAFT - needs human review"})
    pd.DataFrame(coded).to_csv(os.path.join(ROOT, "analysis", "09_disagreement_codes_DRAFT.csv"), index=False)
    pd.concat([wrong.assign(kind="wrong"), right.assign(kind="right")])[["kind", "a_id", "b_id", "winner_id", "loser_id", "conf", "reason"]].to_csv(os.path.join(ROOT, "analysis", "09_gallery_pairs.csv"), index=False)
    print(f"wrong (conf>={MIN_CONF}): {len(wrong)}, right: {len(right)}; draft codes:")
    print(pd.DataFrame(coded)["draft_code"].value_counts().to_string(), f"\nspend ${total_spend():.3f}")


if __name__ == "__main__":
    main()
