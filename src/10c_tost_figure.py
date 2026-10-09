"""Figure 2: pre-registered equivalence test, judge minus image-blind baseline (P1, 90% CI)."""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from decimal import Decimal, ROUND_HALF_UP  # noqa: E402


def r1(x: float) -> float:
    return float(Decimal(f"{float(x):.6f}").quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(ROOT, "analysis")
FIG = os.path.join(ROOT, "figures")
RED, NAVY, SLATE, INK = "#E60023", "#0a3069", "#64748b", "#1f2937"
LABELS = {"gpt-5": "gpt-5", "haiku-4.5": "Claude Haiku 4.5", "gemini-2.5-flash": "Gemini 2.5 Flash", "sonnet-5.5": "Claude Sonnet 5.5"}
VERDICT = {"equivalent": "equivalent", "inconclusive": "not equiv."}
MARGIN = 4

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 7.5, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.spines.left": False, "xtick.labelsize": 7, "ytick.labelsize": 7.5, "axes.edgecolor": SLATE,
                     "xtick.color": INK, "ytick.color": INK, "pdf.fonttype": 42})


def main() -> None:
    eq = pd.read_csv(os.path.join(A, "08c_equivalence.csv"))
    ns = pd.read_csv(os.path.join(A, "08d_non_superiority.csv")).set_index("judge")
    eq = eq[eq["comparison"].str.endswith("minus baseline")].copy()
    eq["judge"] = eq["comparison"].str.split(" ").str[0]
    rows = []
    for j in ("gemini-2.5-flash", "gpt-5", "haiku-4.5"):
        rows.append((j, "2,000 pairs", eq[(eq["subset"] == "all 2,000 (primary)") & (eq["judge"] == j)].iloc[0]))
    rows.append(("sonnet-5.5", "1,000 pairs", eq[(eq["subset"] == "first 1,000 (frontier set)") & (eq["judge"] == "sonnet-5.5")].iloc[0]))

    fig, ax = plt.subplots(figsize=(3.4, 1.75))
    ax.axvspan(-MARGIN, MARGIN, color=SLATE, alpha=0.10, lw=0)
    ax.axvline(0, color=NAVY, lw=0.9)
    ax.axvline(MARGIN, color=SLATE, lw=0.6, ls=(0, (2, 2)))
    ax.axvline(-MARGIN, color=SLATE, lw=0.6, ls=(0, (2, 2)))
    for i, (j, tag, r) in enumerate(rows[::-1]):
        d, lo, hi = r["diff"] * 100, r["ci90_lo"] * 100, r["ci90_hi"] * 100
        ax.plot([lo, hi], [i, i], color=RED, lw=1.6, solid_capstyle="butt")
        ax.plot(d, i, "o", color=RED, ms=4, mec="white", mew=0.6, zorder=3)
        ax.text(d, i + 0.2, f"{r1(d):+.1f}".replace("-", "−"), ha="center", va="bottom", fontsize=6.8, color=INK)
        p = ns.loc[j, "p_upper_vs_+4pts"]
        ptxt = f"p = {p:.3f}".replace("0.", ".") if p >= 0.001 else "p < .001"
        ax.text(4.3, i, VERDICT[r["verdict_margin_4pts"]], va="center", ha="left", fontsize=6.6, color=SLATE)
    ax.set_yticks(range(len(rows)), [f"{LABELS[j]}  ({tag})" for j, tag, _ in rows[::-1]])
    ax.tick_params(axis="y", length=0)
    ax.set_xlim(-7, 7.6)
    ax.set_ylim(-0.6, len(rows) - 0.25)
    ax.set_xticks(range(-6, 5, 2))
    ax.set_xlabel("Judge minus baseline (accuracy points, 90% CI)", color=INK)
    ax.text(0.15, len(rows) - 0.45, "baseline", fontsize=6.6, color=NAVY, va="bottom")
    ax.text(-MARGIN - 0.15, len(rows) - 0.45, "−4", fontsize=6.6, color=SLATE, va="bottom", ha="right")
    ax.text(MARGIN + 0.15, len(rows) - 0.45, "+4", fontsize=6.6, color=SLATE, va="bottom")
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(FIG, f"fig7_tost.{ext}"), dpi=300, bbox_inches="tight", pad_inches=0.02)


if __name__ == "__main__":
    main()
