import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(ROOT, "analysis")
FIG = os.path.join(ROOT, "figures")
RED, NAVY, TEAL, SLATE = "#E60023", "#0a3069", "#0d9488", "#64748b"
JUDGE_COLORS = {"gpt-5": RED, "haiku-4.5": NAVY, "gemini-2.5-flash": TEAL}

plt.rcParams.update({
    "figure.facecolor": "white", "axes.facecolor": "white", "font.size": 8, "axes.titlesize": 9, "axes.labelsize": 8,
    "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 7, "axes.spines.top": False, "axes.spines.right": False,
})


def save(fig: plt.Figure, name: str) -> None:
    os.makedirs(FIG, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(FIG, f"{name}.{ext}"), dpi=300, bbox_inches="tight")
    plt.close(fig)


def pipeline() -> None:
    steps = [
        ("beautiVis\n52,836 charts", "r/dataisbeautiful\n2012-2025"),
        ("Cleaning\n34,556 posts", "blank, small, low-score,\nduplicate, placeholder"),
        ("Pairing\nsame week + type", "clear: winner >= 5x loser\nclose: 1.5-2.5x"),
        ("Judges\n3 LLMs x P1/P2/P3", "both orders for pairwise"),
        ("Analysis", "vs image-blind baseline,\nbiases, gallery"),
    ]
    fig, ax = plt.subplots(figsize=(7.2, 1.5))
    ax.set_axis_off()
    w, gap = 1.25, 0.2
    for i, (head, sub) in enumerate(steps):
        x = i * (w + gap)
        ax.add_patch(FancyBboxPatch((x, 0.2), w, 0.9, boxstyle="round,pad=0.02,rounding_size=0.06", fc="white", ec=RED if i == 3 else NAVY, lw=1.2))
        ax.text(x + w / 2, 0.82, head, ha="center", va="center", fontsize=7.5, weight="bold", color=NAVY)
        ax.text(x + w / 2, 0.42, sub, ha="center", va="center", fontsize=6.2, color=SLATE)
        if i < len(steps) - 1:
            ax.annotate("", xy=(x + w + gap - 0.02, 0.65), xytext=(x + w + 0.02, 0.65), arrowprops=dict(arrowstyle="->", color=SLATE, lw=1))
    ax.set_xlim(-0.05, len(steps) * (w + gap))
    ax.set_ylim(0.1, 1.2)
    save(fig, "fig1_pipeline")


def accuracy_dots() -> None:
    t = pd.read_csv(os.path.join(A, "08_main_table.csv"))
    t = t[t["set"] == "clear"].copy()
    base = t[t["row"] == "feature baseline (OOF)"].iloc[0]
    t = t[t["row"] != "feature baseline (OOF)"].sort_values("accuracy")
    fig, ax = plt.subplots(figsize=(4.6, 0.32 * len(t) + 0.8))
    ax.axvspan(base["acc_lo"], base["acc_hi"], color=SLATE, alpha=0.15, lw=0)
    ax.axvline(base["accuracy"], color=SLATE, lw=0.8)
    ax.text(base["accuracy"], len(t) - 0.35, " image-blind baseline", color=SLATE, fontsize=6.5, va="bottom")
    ax.axvline(0.5, color="black", lw=0.6, ls=":")
    for i, (_, r) in enumerate(t.iterrows()):
        color = JUDGE_COLORS.get(r["row"].split(" ")[0], SLATE)
        ax.errorbar(r["accuracy"], i, xerr=[[r["accuracy"] - r["acc_lo"]], [r["acc_hi"] - r["accuracy"]]], fmt="o", color=color, ms=4, capsize=2, lw=1)
    ax.set_yticks(range(len(t)), [f"{r} (n={n})" for r, n in zip(t["row"], t["n_pairs"])])
    ax.set_xlabel("Clear-pair accuracy (95% bootstrap CI)")
    ax.set_xlim(0.4, max(0.8, t["acc_hi"].max() + 0.02))
    save(fig, "fig2_accuracy")


def by_year() -> None:
    b = pd.read_csv(os.path.join(A, "08_breakdowns.csv"))
    b = b[(b["dimension"] == "year_bin") & b["row"].str.endswith(" P1")]
    order = ["2012-15", "2016-19", "2020-22", "2023-25"]
    fig, ax = plt.subplots(figsize=(4.2, 2.6))
    for row, g in b.groupby("row"):
        g = g.set_index("level").reindex(order)
        judge = row.split(" ")[0]
        ax.plot(order, g["accuracy"], marker="o", ms=3, color=JUDGE_COLORS.get(judge, SLATE), lw=1.2)
        ax.annotate(f"{judge} {g['accuracy'].iloc[-1]:.2f}", (len(order) - 1, g["accuracy"].iloc[-1]), xytext=(5, 0), textcoords="offset points", fontsize=6.5, va="center", color=JUDGE_COLORS.get(judge, SLATE))
    ax.axhline(0.5, color="black", lw=0.6, ls=":")
    ax.set_ylabel("Clear-pair accuracy, P1 score difference")
    ax.set_xlim(-0.2, len(order) - 0.2 + 1.2)
    save(fig, "fig3_accuracy_by_year")


def bias_dumbbell(judge_row: str) -> None:
    t = pd.read_csv(os.path.join(A, "08_bias_probes.csv"))
    aud = t[t["target"] == "audience"].set_index("feature")["coef"]
    jud = t[t["target"] == judge_row].set_index("feature")["coef"]
    feats = aud.index.tolist()
    labels = {"log_ocr_words": "text amount (log OCR words)", "n_colors": "dominant colors", "edge_density": "edge density", "log_aspect_ratio": "aspect ratio (log)", "log_orig_megapixels": "original resolution (log)"}
    fig, ax = plt.subplots(figsize=(3.4, 2.1))
    for i, f in enumerate(feats):
        ax.plot([aud[f], jud[f]], [i, i], color=SLATE, lw=1)
    ax.scatter(aud.values, range(len(feats)), color=NAVY, s=18, label="audience winner", zorder=3)
    ax.scatter(jud.reindex(feats).values, range(len(feats)), color=RED, s=18, label=f"judge pick ({judge_row})", zorder=3)
    ax.axvline(0, color="black", lw=0.6, ls=":")
    ax.set_yticks(range(len(feats)), [labels.get(f, f) for f in feats])
    ax.set_xlabel("Logistic coefficient on A-minus-B difference (per SD)")
    ax.legend(loc="upper center", bbox_to_anchor=(0.35, -0.28), ncol=2, frameon=False)
    save(fig, "fig4_bias_dumbbell")


def main(best_row: str) -> None:
    pipeline()
    accuracy_dots()
    by_year()
    bias_dumbbell(best_row)


if __name__ == "__main__":
    import sys

    main(sys.argv[1] if len(sys.argv) > 1 else "gpt-5 P1")


def paired_diffs() -> None:
    t = pd.read_csv(os.path.join(A, "08_main_table.csv"))
    t = t[(t["set"] == "clear") & t["diff_vs_baseline"].notna()].sort_values("diff_vs_baseline")
    fig, ax = plt.subplots(figsize=(3.4, 0.26 * len(t) + 0.7))
    ax.axvline(0, color=SLATE, lw=0.8)
    for i, (_, r) in enumerate(t.iterrows()):
        color = JUDGE_COLORS.get(r["row"].split(" ")[0], SLATE)
        ax.errorbar(r["diff_vs_baseline"] * 100, i, xerr=[[(r["diff_vs_baseline"] - r["diff_lo"]) * 100], [(r["diff_hi"] - r["diff_vs_baseline"]) * 100]], fmt="o", color=color, ms=3.5, capsize=2, lw=1)
    ax.set_yticks(range(len(t)), [f"{r} (n={n})" for r, n in zip(t["row"], t["n_pairs"])])
    ax.set_xlabel("Judge minus image-blind baseline, same pairs (accuracy points, 95% CI)")
    save(fig, "fig6_paired_diff")


if __name__ == "__main__":
    paired_diffs()
