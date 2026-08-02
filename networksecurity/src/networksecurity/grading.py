"""
grading.py -- statistical scoring and citation-quality grading.

wilson_ci() is used everywhere a percentage is reported in this project,
instead of a plain successes/n ratio -- it's much better calibrated than a
normal approximation at small n, which matters a lot given some pilot runs
use samples as small as n=5/class.

grade_citation() implements the citation-quality rubric: given a model's
cited reference_id and the true class, decide whether that citation is a
real, correctly-matched reference; a real but too-broad/generic one; a real
ID describing the wrong attack family; no citation at all; or an
unverified ID not yet checked against MITRE/NVD.
"""

import os

from .corpus import CVE_CORPUS, known_reference_map, generic_ids, wrong_family_ids


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


def grade_citation(true_class, reference_id, benign_class):
    """Grade a single citation. Returns one of: n/a-benign, no-citation,
    real-and-correct, real-but-generic, real-but-wrong-family, or an
    UNVERIFIED-prefixed string for IDs not in the corpus at all."""
    if true_class == benign_class:
        return "n/a-benign"
    ref = str(reference_id).strip()
    if ref.upper() in ("N/A", "NAN", "NONE", ""):
        return "no-citation"
    known_refs = known_reference_map()
    if ref in wrong_family_ids():
        return "real-but-wrong-family"
    if ref in generic_ids():
        return "real-but-generic"
    if ref not in known_refs:
        return "UNVERIFIED (not yet checked against MITRE/NVD -- verify manually before citing in a paper)"
    if true_class in known_refs[ref]:
        return "real-and-correct"
    return "real-but-wrong-family"


def score_and_summarize(harness_results, baseline_results, benign_class, out_dir):
    """Prints (and returns as a list of lines, also written to summary.txt)
    the same accuracy / citation-quality / baseline tables as the original
    research harness."""
    lines = []

    def log(s=""):
        print(s)
        lines.append(s)

    if harness_results is not None:
        harness_results = harness_results.copy()
        harness_results["correct"] = (harness_results["classification"].str.strip()
                                       == harness_results["true_class"].str.strip())
        log("=== Claude classification accuracy by condition (Wilson 95% CI) ===")
        for cond, g in harness_results.groupby("condition"):
            log(f"  {cond:>18}: {fmt_ci(int(g['correct'].sum()), len(g))}")

        harness_results["citation_grade"] = harness_results.apply(
            lambda r: grade_citation(r["true_class"], r["reference_id"], benign_class), axis=1)
        log("\n=== Citation quality by condition (counts, and 95% CI on 'real-and-correct' rate "
            "among attack samples) ===")
        for cond, g in harness_results.groupby("condition"):
            log(f"\n  {cond}:")
            log("  " + str(g["citation_grade"].value_counts()).replace("\n", "\n  "))
            attack_g = g[g["true_class"] != benign_class]
            n_attack = len(attack_g)
            n_correct = int((attack_g["citation_grade"] == "real-and-correct").sum())
            n_unverified = int(attack_g["citation_grade"].str.startswith("UNVERIFIED").sum())
            log(f"  -> real-and-correct rate among attack samples: {fmt_ci(n_correct, n_attack)}")
            if n_unverified:
                log(f"  -> WARNING: {n_unverified} citation(s) reference an ID not in the "
                    f"verified corpus -- check these against capec.mitre.org/nvd.nist.gov "
                    f"before treating them as fabricated OR as correct.")

    if baseline_results is not None:
        log("\n=== Non-LLM baseline detectors (Wilson 95% CI on recall) ===")
        for col, name in [("zscore_flagged_attack", "Rolling z-score"),
                           ("isoforest_flagged_attack", "Isolation Forest")]:
            tp = ((baseline_results[col]) & (baseline_results.true_is_attack)).sum()
            fp = ((baseline_results[col]) & (~baseline_results.true_is_attack)).sum()
            fn = ((~baseline_results[col]) & (baseline_results.true_is_attack)).sum()
            tn = ((~baseline_results[col]) & (~baseline_results.true_is_attack)).sum()
            n_attack = tp + fn
            acc = (tp + tn) / len(baseline_results)
            prec = tp / (tp + fp) if tp + fp else 0
            rec = tp / (tp + fn) if tp + fn else 0
            f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0
            log(f"{name:>18}: acc={acc:.2f} precision={prec:.2f} "
                f"recall={fmt_ci(int(tp), int(n_attack))} f1={f1:.2f} (TP={tp} FP={fp} FN={fn} TN={tn})")

    with open(os.path.join(out_dir, "summary.txt"), "w") as f:
        f.write("\n".join(lines))
    return lines
