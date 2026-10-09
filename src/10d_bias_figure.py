import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(ROOT, "analysis")
FIG = os.path.join(ROOT, "figures")
RED, NAVY, TEAL, PURPLE = "#E60023", "#0a3069", "#0d9488", "#7c3aed"
FEATURES = {"log_ocr_words": "text amount (log OCR words)", "log_orig_megapixels": "original resolution (log)", "n_colors": "dominant colors",
            "edge_density": "edge density", "log_aspect_ratio": "aspect ratio (log)"}
SERIES = [("audience", "audience winner", "black", "D", "2000"), ("gpt-5 P1", "gpt-5", RED, "o", "2000"), ("haiku-4.5 P1", "Claude Haiku 4.5", NAVY, "o", "2000"),
          ("gemini-2.5-flash P1", "Gemini 2.5 Flash", TEAL, "o", "2000"), ("sonnet-5.5 P1", "Claude Sonnet 5.5", PURPLE, "o", "1000")]

plt.rcParams.update({"font.size": 7, "axes.spines.top": False, "axes.spines.right": False, "xtick.labelsize": 6.5, "ytick.labelsize": 6.5, "legend.fontsize": 6})


def main() -> None:
    b2 = pd.read_csv(os.path.join(A, "08c_bias_probes_2000.csv"))
    b1 = pd.read_csv(os.path.join(A, "08c_bias_probes_1000.csv"))
    fig, ax = plt.subplots(figsize=(3.4, 2.5))
    ax.axvline(0, color="#64748b", lw=0.7, ls=":")
    feats = list(FEATURES)
    for k, (target, label, color, marker, n) in enumerate(SERIES):
        t = (b2 if n == "2000" else b1)
        t = t[t["target"] == target].set_index("feature")
        y = [i + (k - 2) * 0.13 for i in range(len(feats))]
        ax.errorbar(t.loc[feats, "coef"], y, xerr=1.96 * t.loc[feats, "se"], fmt=marker, color=color, ms=3.2 if marker == "o" else 3.8, lw=0.8, capsize=1.5,
                    label=f"{label} ({n} pairs)")
    ax.set_yticks(range(len(feats)), [FEATURES[f] for f in feats])
    ax.invert_yaxis()
    ax.set_xlabel("Logistic coefficient per SD of A-minus-B difference (95% CI)")
    ax.legend(loc="upper center", bbox_to_anchor=(0.3, -0.22), ncol=2, frameon=False)
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(FIG, f"fig8_bias_all.{ext}"), dpi=300, bbox_inches="tight")


if __name__ == "__main__":
    main()
