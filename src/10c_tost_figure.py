import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(ROOT, "analysis")
FIG = os.path.join(ROOT, "figures")
RED, NAVY, TEAL, SLATE, PURPLE = "#E60023", "#0a3069", "#0d9488", "#64748b", "#7c3aed"
COLORS = {"gpt-5": RED, "haiku-4.5": NAVY, "gemini-2.5-flash": TEAL, "sonnet-5.5": PURPLE}
LABELS = {"gpt-5": "gpt-5", "haiku-4.5": "Claude Haiku 4.5", "gemini-2.5-flash": "Gemini 2.5 Flash", "sonnet-5.5": "Claude Sonnet 5.5"}
MARGIN = 4

plt.rcParams.update({"font.size": 7, "axes.spines.top": False, "axes.spines.right": False, "xtick.labelsize": 6.5, "ytick.labelsize": 6.5})


def main() -> None:
    eq = pd.read_csv(os.path.join(A, "08c_equivalence.csv"))
    eq = eq[eq["comparison"].str.endswith("minus baseline")].copy()
    eq["judge"] = eq["comparison"].str.split(" ").str[0]
    rows = []
    for subset, tag in (("all 2,000 (primary)", "2,000 pairs"), ("first 1,000 (frontier set)", "1,000 pairs")):
        sub = eq[eq["subset"] == subset]
        for j in ("gemini-2.5-flash", "gpt-5", "haiku-4.5", "sonnet-5.5"):
            r = sub[sub["judge"] == j]
            if len(r) and not (subset.startswith("first") and j != "sonnet-5.5"):
                rows.append((f"{LABELS[j]} ({tag})", j, r.iloc[0]))
    fig, ax = plt.subplots(figsize=(3.4, 0.30 * len(rows) + 0.75))
    ax.axvspan(-MARGIN, MARGIN, color=SLATE, alpha=0.12, lw=0)
    ax.axvline(0, color=SLATE, lw=0.8)
    for i, (label, j, r) in enumerate(rows[::-1]):
        ax.errorbar(r["diff"] * 100, i, xerr=[[(r["diff"] - r["ci90_lo"]) * 100], [(r["ci90_hi"] - r["diff"]) * 100]], fmt="o", color=COLORS[j], ms=3.5, capsize=2, lw=1.1)
        ax.text(MARGIN + 0.3, i, r["verdict_margin_4pts"], va="center", fontsize=6, color=SLATE)
    ax.set_yticks(range(len(rows)), [r[0] for r in rows[::-1]])
    ax.set_xlim(-8, 7.5)
    ax.set_xlabel("P1 judge minus image-blind baseline (accuracy points, 90% CI)")
    ax.text(0, len(rows) - 0.35, "±4-point equivalence margin", ha="center", fontsize=6, color=SLATE)
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(FIG, f"fig7_tost.{ext}"), dpi=300, bbox_inches="tight")


if __name__ == "__main__":
    main()
