import os
import textwrap

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from PIL import Image  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(ROOT, "figures")
RED, NAVY, SLATE = "#E60023", "#0a3069", "#64748b"
THUMB_PX = 360  # Reddit images are shown as small thumbnails for commentary, never at full resolution

# gpt-5 P3 confident misses (both orders wrong). Quotes are the AB-order reason; "Chart A/B" is replaced by a bracketed referent.
EXAMPLES = [
    ("2016-12-0322", "2016-12-0332", "[The judge's pick] clearly labels axes, units, and metrics with readable scales and context, ... while [the winner] is aesthetically nice but ambiguous and lacks labels or clear meaning."),
    ("2014-10-0099", "2014-10-0121", "[The judge's pick] is clearer and more polished with consistent labeling, color legend, and context ..., whereas [the winner] is cluttered, low-resolution, and uses distracting markers that obscure the trend."),
    ("2018-04-0154", "2018-04-0155", "[The judge's pick] uses consistent labeling, colors, and scales to clearly show monthly totals and category breakdowns, whereas [the winner] has cluttered slanted labels, unclear axis meaning, and weaker design aesthetics."),
    ("2017-04-0358", "2017-04-0301", "[The judge's pick] clearly communicates data with labeled choropleths and legends, while [the winner] is an abstract line rendering that looks artistic but is hard to interpret or quantify."),
]

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 6.5})


def short(title: str, width: int = 34) -> str:
    lines = textwrap.wrap(title.replace("[OC]", "").strip(), width)
    return "\n".join(lines[:2]) + ("…" if len(lines) > 2 else "")


P1_FILES = [("gpt-5", "gpt-5__P1__clear2000.csv"), ("Haiku", "haiku-4.5__P1__clear2000.csv"), ("Flash", "gemini-2.5-flash__P1__clear2000.csv"), ("Sonnet", "sonnet-5.5__P1__clear1000.csv")]


def p1_scores() -> dict[str, pd.Series]:
    return {name: pd.read_csv(os.path.join(ROOT, "judges", "parsed", f)).set_index("post_id")["score"] for name, f in P1_FILES}


def main() -> None:
    posts = pd.read_parquet(os.path.join(ROOT, "data", "clean", "posts.parquet")).set_index("post_id")
    p1 = p1_scores()
    fig = plt.figure(figsize=(7.0, 5.6))
    outer = fig.add_gridspec(2, 2, wspace=0.08, hspace=0.22, left=0.02, right=0.98, top=0.965, bottom=0.02)
    for k, (win, pick, quote) in enumerate(EXAMPLES):
        cell = outer[k // 2, k % 2].subgridspec(3, 2, height_ratios=[0.30, 1, 0.40], wspace=0.08, hspace=0.12)
        for j, (pid, role, color) in enumerate(((win, "Audience winner", NAVY), (pick, "Judge's pick", RED))):
            p = posts.loc[pid]
            head = fig.add_subplot(cell[0, j])
            head.set_axis_off()
            head.text(0, 0.62, f"{role}\n{int(p['score']):,} votes · month pct {p['pct_month']:.2f}", color=color, weight="bold", fontsize=5.8, va="center", linespacing=1.3)
            scores = " / ".join(f"{p1[n][pid]:g}" for n, _ in P1_FILES)
            head.text(0, -0.05, f"P1 scores: {scores}", color=color, fontsize=5.6, va="center")
            ax = fig.add_subplot(cell[1, j])
            im = Image.open(os.path.join(ROOT, "data", "images_std", f"{pid}.jpg"))
            im.thumbnail((THUMB_PX, THUMB_PX))
            ax.imshow(im)
            ax.set_xticks([])
            ax.set_yticks([])
            for s in ax.spines.values():
                s.set_color(color)
                s.set_linewidth(1.2)
            ax.set_xlabel(short(p["json_title"]), fontsize=5.5, color="black", labelpad=2)
        qa = fig.add_subplot(cell[2, :])
        qa.set_axis_off()
        qa.text(0, 0.35, "\n".join(textwrap.wrap(f"gpt-5 (P3; wrong in both orders): “{quote}”", 88)), fontsize=5.3, color=SLATE, style="italic", va="center")
        fig.text(outer[k // 2, k % 2].get_position(fig).x0, outer[k // 2, k % 2].get_position(fig).y1 + 0.004, "abcd"[k], weight="bold", fontsize=9)
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(FIG, f"fig5_examples.{ext}"), dpi=300)
    plt.close(fig)


if __name__ == "__main__":
    main()
