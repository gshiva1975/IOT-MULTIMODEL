#!/usr/bin/env python3
"""
create_report.py -- build a full report (charts + a markdown summary) from
an ALREADY-GRADED results CSV -- i.e. the output of generate_rag_report.py
(has citation_grade, correct, true_class, classification, reference_id,
justification columns already computed).

Self-contained on purpose: does not import the networksecurity package, the
original harness_results.csv, the viz manifest, or the CVE corpus -- since
the input CSV already carries its own grading, this script only needs
pandas + matplotlib to turn it into a report. That also means it works on
any already-graded CSV you hand it, from any machine, without needing the
rest of the project alongside it.

Usage:
    python3 create_report.py --csv rag_grounded_results.csv --out report/
    python3 create_report.py --csv rag_grounded_results.csv --out report/ --title "RAG-Grounded Pilot"

Outputs (under --out):
    report.md              -- written summary: accuracy, citation-quality table, per-class
                               breakdown, and every sample's classification + citation + justification
    citation_quality.png   -- bar chart of citation_grade counts
    accuracy_overall.png   -- overall classification accuracy, Wilson 95% CI
    accuracy_by_class.png  -- per-class accuracy, Wilson 95% CI (only written if >1 class present)
"""

import argparse
import os
import sys

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

GRADE_COLORS = {
    "real-and-correct": "#2e7d32",
    "real-but-generic": "#f9a825",
    "real-but-wrong-family": "#e64a19",
    "no-citation": "#9e9e9e",
    "UNVERIFIED": "#455a64",
    "n/a-benign": "#cfd8dc",
}
GRADE_ORDER = list(GRADE_COLORS.keys())


def wilson_ci(successes, n, z=1.96):
    """Wilson score interval for a binomial proportion. Returns
    (point_estimate, lo, hi) as fractions in [0, 1]."""
    if n == 0:
        return (float("nan"), float("nan"), float("nan"))
    p = successes / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    half = (z * ((p * (1 - p) / n + z**2 / (4 * n**2)) ** 0.5)) / denom
    return (p, max(0.0, center - half), min(1.0, center + half))


def fmt_ci(successes, n):
    p, lo, hi = wilson_ci(successes, n)
    return f"{p*100:.1f}% [{lo*100:.1f}-{hi*100:.1f}%] (n={n})"


def bar_with_ci(ax, labels, stats, color, ylabel, title):
    xs = range(len(stats))
    heights = [s[0] * 100 for s in stats]
    err_lo = [max(0.0, (s[0] - s[1]) * 100) for s in stats]
    err_hi = [max(0.0, (s[2] - s[0]) * 100) for s in stats]
    ax.bar(xs, heights, yerr=[err_lo, err_hi], capsize=6, color=color, width=0.55)
    ax.set_xticks(list(xs))
    ax.set_xticklabels(labels)
    ax.set_ylabel(ylabel)
    ax.set_ylim(0, 112)
    ax.set_title(title)
    for i, s in enumerate(stats):
        ax.text(i, heights[i] + err_hi[i] + 2, f"n={s[3]}", ha="center", fontsize=9, color="#555")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv", required=True, help="path to an already-graded results CSV "
                     "(needs at minimum: sample_id, true_class, classification, reference_id, "
                     "citation_grade, correct; condition and justification are used if present)")
    ap.add_argument("--out", default="report", help="folder to write report.md + charts to")
    ap.add_argument("--title", default=None, help="report title (default: derived from --csv filename)")
    args = ap.parse_args()

    if not os.path.isfile(args.csv):
        sys.exit(f"Not found: {args.csv}")

    df = pd.read_csv(args.csv)
    required = {"true_class", "classification", "citation_grade", "correct"}
    missing = required - set(df.columns)
    if missing:
        sys.exit(f"--csv is missing required column(s): {sorted(missing)}. This script expects an "
                  f"ALREADY-GRADED results CSV (the output of generate_rag_report.py), not raw "
                  f"harness_results.csv.")

    os.makedirs(args.out, exist_ok=True)
    condition = df["condition"].iloc[0] if "condition" in df.columns and len(df) else "unknown"
    title = args.title or f"{condition} report ({os.path.basename(args.csv)})"

    # normalize correct to bool (CSV round-trips can turn it into the string "True"/"False")
    df["correct"] = df["correct"].astype(str).str.strip().str.lower().isin(["true", "1"])

    # ---------- chart 1: citation quality ----------
    counts = df["citation_grade"].value_counts()
    grades_present = [g for g in GRADE_ORDER if g in counts.index]
    grades_present += [g for g in counts.index if g not in grades_present]  # any unexpected grade values too
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.bar(grades_present, [counts[g] for g in grades_present],
           color=[GRADE_COLORS.get(g, "#607d8b") for g in grades_present])
    ax.set_ylabel("Number of samples")
    ax.set_title(f"{condition} citation quality (n={len(df)})")
    plt.setp(ax.get_xticklabels(), rotation=20, ha="right")
    fig.tight_layout()
    fig.savefig(os.path.join(args.out, "citation_quality.png"), dpi=150)
    plt.close(fig)

    # ---------- chart 2: overall accuracy ----------
    p, lo, hi = wilson_ci(int(df["correct"].sum()), len(df))
    err_lo, err_hi = max(0.0, (p - lo) * 100), max(0.0, (hi - p) * 100)
    fig, ax = plt.subplots(figsize=(4, 4.5))
    ax.bar([condition], [p * 100], yerr=[[err_lo], [err_hi]], capsize=6, color="#2e74b5", width=0.5)
    ax.set_ylim(0, 112)
    ax.set_ylabel("Classification accuracy (%)")
    ax.set_title(f"Overall accuracy (Wilson 95% CI, n={len(df)})")
    ax.text(0, p * 100 + err_hi + 2, f"n={len(df)}", ha="center", fontsize=9, color="#555")
    fig.tight_layout()
    fig.savefig(os.path.join(args.out, "accuracy_overall.png"), dpi=150)
    plt.close(fig)

    # ---------- chart 3: per-class accuracy (only if >1 class) ----------
    classes = sorted(df["true_class"].unique())
    if len(classes) > 1:
        stats = []
        for cls in classes:
            g = df[df["true_class"] == cls]
            pc, loc, hic = wilson_ci(int(g["correct"].sum()), len(g))
            stats.append((pc, loc, hic, len(g)))
        fig, ax = plt.subplots(figsize=(max(7, len(classes) * 0.6), 5.5))
        bar_with_ci(ax, classes, stats, "#2e74b5", "Classification accuracy (%)",
                    f"{condition} accuracy by class (Wilson 95% CI)")
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
        fig.tight_layout()
        fig.savefig(os.path.join(args.out, "accuracy_by_class.png"), dpi=150)
        plt.close(fig)

    # ---------- report.md ----------
    lines = [f"# {title}", ""]
    lines.append(f"**Samples:** {len(df)}  ")
    lines.append(f"**Classes:** {', '.join(classes)}  ")
    lines.append(f"**Condition:** {condition}  ")
    lines.append("")
    lines.append(f"## Accuracy")
    lines.append("")
    lines.append(f"Overall classification accuracy: **{fmt_ci(int(df['correct'].sum()), len(df))}**")
    lines.append("")
    lines.append("![accuracy](accuracy_overall.png)")
    lines.append("")
    if len(classes) > 1:
        lines.append("| Class | Accuracy (Wilson 95% CI) | n |")
        lines.append("|---|---|---|")
        for cls in classes:
            g = df[df["true_class"] == cls]
            lines.append(f"| {cls} | {fmt_ci(int(g['correct'].sum()), len(g))} | {len(g)} |")
        lines.append("")
        lines.append("![accuracy by class](accuracy_by_class.png)")
        lines.append("")

    lines.append("## Citation quality")
    lines.append("")
    lines.append("| Grade | Count | Share |")
    lines.append("|---|---|---|")
    for g in grades_present:
        c = int(counts[g])
        lines.append(f"| {g} | {c} | {c/len(df)*100:.1f}% |")
    lines.append("")
    n_correct = int((df["citation_grade"] == "real-and-correct").sum())
    lines.append(f"Real-and-correct rate: **{fmt_ci(n_correct, len(df))}**")
    lines.append("")
    lines.append("![citation quality](citation_quality.png)")
    lines.append("")

    lines.append("## Per-sample results")
    lines.append("")
    lines.append("| sample_id | true_class | classification | reference_id | citation_grade |")
    lines.append("|---|---|---|---|---|")
    for _, r in df.iterrows():
        lines.append(f"| {r['sample_id']} | {r['true_class']} | {r['classification']} | "
                      f"{r.get('reference_id', '')} | {r['citation_grade']} |")
    lines.append("")

    if "justification" in df.columns:
        lines.append("## Example justifications")
        lines.append("")
        for _, r in df.head(3).iterrows():
            lines.append(f"**{r['sample_id']}** ({r['citation_grade']}): {r['justification']}")
            lines.append("")

    with open(os.path.join(args.out, "report.md"), "w") as f:
        f.write("\n".join(lines))

    print(f"Wrote report to {args.out}/:")
    print("  report.md")
    print("  citation_quality.png")
    print("  accuracy_overall.png")
    if len(classes) > 1:
        print("  accuracy_by_class.png")


if __name__ == "__main__":
    main()
