"""
grading.py -- statistical scoring: is 2D or 3D more accurate, and is the
difference (if any) larger than sampling noise at this n. Same Wilson-CI
approach as ../networksecurity, for the same reason -- plain ratios
overstate confidence at small pilot sample sizes.
"""

import os


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


def score_and_summarize(harness_results, out_dir):
    """Prints (and returns as a list of lines, also written to summary.txt)
    accuracy by dimensionality, overall and per-class, plus a same-sample
    paired comparison (does 2D and 3D agree on each sample, and when they
    disagree, which one was right)."""
    lines = []

    def log(s=""):
        print(s)
        lines.append(s)

    df = harness_results.copy()
    df["correct"] = (df["classification"].astype(str).str.strip()
                      == df["true_class"].astype(str).str.strip())

    log("=== Accuracy by dimensionality (Wilson 95% CI) ===")
    for dim, g in df.groupby("dimensionality"):
        log(f"  {dim:>4}: {fmt_ci(int(g['correct'].sum()), len(g))}")

    log("\n=== Accuracy by class and dimensionality ===")
    for cls, g in df.groupby("true_class"):
        parts = []
        for dim in sorted(g["dimensionality"].unique()):
            gg = g[g["dimensionality"] == dim]
            parts.append(f"{dim}={fmt_ci(int(gg['correct'].sum()), len(gg))}")
        log(f"  {cls}: " + " | ".join(parts))

    # Paired comparison: for samples where both dimensionalities completed,
    # how often did they agree, and when they disagreed, which one was
    # correct? This is the more statistically informative comparison at
    # small n, since it controls for per-sample difficulty.
    pivot = df[df["classification"] != "ERROR"].pivot_table(
        index=["sample_id", "true_class"], columns="dimensionality",
        values="classification", aggfunc="first").reset_index()
    if "2d" in pivot.columns and "3d" in pivot.columns:
        paired = pivot.dropna(subset=["2d", "3d"])
        agree = (paired["2d"] == paired["3d"]).sum()
        only_2d_right = ((paired["2d"] == paired["true_class"]) & (paired["3d"] != paired["true_class"])).sum()
        only_3d_right = ((paired["3d"] == paired["true_class"]) & (paired["2d"] != paired["true_class"])).sum()
        both_right = ((paired["2d"] == paired["true_class"]) & (paired["3d"] == paired["true_class"])).sum()
        log(f"\n=== Paired comparison ({len(paired)} samples with both dimensionalities completed) ===")
        log(f"  Both correct: {both_right}")
        log(f"  Only 2D correct: {only_2d_right}")
        log(f"  Only 3D correct: {only_3d_right}")
        log(f"  Both wrong: {len(paired) - both_right - only_2d_right - only_3d_right}")
        log(f"  2D and 3D gave the same classification: {agree}/{len(paired)}")

    with open(os.path.join(out_dir, "summary.txt"), "w") as f:
        f.write("\n".join(lines))
    return lines
