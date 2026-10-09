"""Figure 3: image features that predict the audience winner vs each judge's P1 pick."""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(ROOT, "analysis")
FIG = os.path.join(ROOT, "figures")
RED, NAVY, SLATE, INK = "#E60023", "#0a3069", "#64748b", "#1f2937"
FEATURES = {"log_ocr_words": "Text amount\n(log OCR words)", "log_orig_megapixels": "Original resolution\n(log megapixels)",
            "n_colors": "Dominant colors", "edge_density": "Edge density", "log_aspect_ratio": "Aspect ratio (log)"}
# (target, legend label, color, marker, pair set)
SERIES = [("audience", "Audience winner", NAVY, "D", "2000"),
          ("gpt-5 P1", "gpt-5", RED, "o", "2000"),
          ("haiku-4.5 P1", "Claude Haiku 4.5", RED, "s", "2000"),
          ("gemini-2.5-flash P1", "Gemini 2.5 Flash", RED, "^", "2000"),
          ("sonnet-5.5 P1", "Claude Sonnet 5.5", RED, "v", "1000")]

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 7.5, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.spines.left": False, "xtick.labelsize": 7, "ytick.labelsize": 7.3, "legend.fontsize": 6.8,
                     "axes.edgecolor": SLATE, "xtick.color": INK, "ytick.color": INK, "pdf.fonttype": 42})


def main() -> None:
    b2 = pd.read_csv(os.path.join(A, "08c_bias_probes_2000.csv"))
    b1 = pd.read_csv(os.path.join(A, "08c_bias_probes_1000.csv"))
    feats = list(FEATURES)
    fig, ax = plt.subplots(figsize=(3.4, 2.75))
    ax.axhspan(-0.5, 0.5, color=RED, alpha=0.06, lw=0)
    ax.axvline(0, color=SLATE, lw=0.7)
    for k, (target, label, color, marker, n) in enumerate(SERIES):
        t = (b2 if n == "2000" else b1)
        t = t[t["target"] == target].set_index("feature")
        y = [i + (k - 2) * 0.15 for i in range(len(feats))]
        aud = target == "audience"
        ax.errorbar(t.loc[feats, "coef"], y, xerr=1.96 * t.loc[feats, "se"], fmt=marker, color=color,
                    mfc=color if aud else "white", mec=color, ms=3.6 if aud else 3.0, mew=0.9, lw=0.8 if aud else 0.6,
                    capsize=0, label=label, zorder=3 if aud else 2, alpha=1 if aud else 0.9)
    ax.set_yticks(range(len(feats)), [FEATURES[f] for f in feats])
    ax.tick_params(axis="y", length=0)
    ax.invert_yaxis()
    ax.set_xlim(-0.42, 0.72)
    ax.set_xlabel("Coefficient per SD of A-minus-B difference (95% CI)", color=INK)
    ax.text(-0.40, 0.0, "judges reward\ntext; audience\nis neutral", ha="left", va="center", fontsize=6.6, color=RED, linespacing=1.1)
    ax.legend(loc="upper center", bbox_to_anchor=(0.42, -0.2), ncol=3, frameon=False, handletextpad=0.3, columnspacing=1.0)
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(FIG, f"fig8_bias_all.{ext}"), dpi=300, bbox_inches="tight", pad_inches=0.02)


if __name__ == "__main__":
    main()
