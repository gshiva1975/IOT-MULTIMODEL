"""
reporting.py -- charts comparing 2D vs 3D accuracy, overall and by class.
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .grading import wilson_ci


def build_charts(harness_results, out_dir):
    df = harness_results[harness_results["classification"] != "ERROR"].copy()
    df["correct"] = (df["classification"].astype(str).str.strip()
                      == df["true_class"].astype(str).str.strip())

    # ---------- overall accuracy: 2D vs 3D ----------
    dims = sorted(df["dimensionality"].unique())
    stats = []
    for dim in dims:
        g = df[df["dimensionality"] == dim]
        p, lo, hi = wilson_ci(int(g["correct"].sum()), len(g))
        stats.append((p, lo, hi, len(g)))

    fig, ax = plt.subplots(figsize=(4.5, 5))
    xs = range(len(dims))
    heights = [s[0] * 100 for s in stats]
    err_lo = [max(0.0, (s[0] - s[1]) * 100) for s in stats]
    err_hi = [max(0.0, (s[2] - s[0]) * 100) for s in stats]
    ax.bar(xs, heights, yerr=[err_lo, err_hi], capsize=6, color=["#2e74b5", "#c53030"], width=0.5)
    ax.set_xticks(list(xs))
    ax.set_xticklabels([d.upper() for d in dims])
    ax.set_ylabel("Classification accuracy (%)")
    ax.set_ylim(0, 112)
    ax.set_title("Accuracy: 2D vs 3D (Wilson 95% CI)")
    for i, s in enumerate(stats):
        ax.text(i, heights[i] + err_hi[i] + 2, f"n={s[3]}", ha="center", fontsize=9, color="#555")
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "accuracy_2d_vs_3d.png"), dpi=150)
    plt.close(fig)

    # ---------- per-class accuracy, grouped bars ----------
    classes = sorted(df["true_class"].unique())
    if len(classes) > 1:
        fig, ax = plt.subplots(figsize=(max(7, len(classes) * 0.7), 5.5))
        width = 0.35
        colors = {"2d": "#2e74b5", "3d": "#c53030"}
        for i, dim in enumerate(dims):
            heights, err_lo, err_hi = [], [], []
            for cls in classes:
                g = df[(df["true_class"] == cls) & (df["dimensionality"] == dim)]
                p, lo, hi = wilson_ci(int(g["correct"].sum()), len(g)) if len(g) else (0, 0, 0)
                heights.append(p * 100)
                err_lo.append(max(0.0, (p - lo) * 100))
                err_hi.append(max(0.0, (hi - p) * 100))
            xs = [x + i * width for x in range(len(classes))]
            ax.bar(xs, heights, width=width, yerr=[err_lo, err_hi], capsize=3,
                   color=colors.get(dim, "#888"), label=dim.upper())
        ax.set_xticks([x + width / 2 for x in range(len(classes))])
        ax.set_xticklabels(classes, rotation=60, ha="right", fontsize=8)
        ax.set_ylabel("Classification accuracy (%)")
        ax.set_ylim(0, 112)
        ax.set_title("Accuracy by class: 2D vs 3D (Wilson 95% CI)")
        ax.legend()
        fig.tight_layout()
        fig.savefig(os.path.join(out_dir, "accuracy_by_class_2d_vs_3d.png"), dpi=150)
        plt.close(fig)
