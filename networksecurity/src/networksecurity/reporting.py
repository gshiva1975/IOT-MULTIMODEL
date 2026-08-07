"""
reporting.py -- filter harness_results.csv down to one condition (typically
rag_grounded), chart it, and export the exact inputs (traffic images + raw
pcap row-slices) each sample used.

This is a library version of the standalone visualize_rag_grounded.py
script: same behavior, but callable from other code (the CLI script in
scripts/generate_rag_report.py is a thin wrapper around this module).
"""

import os
import shutil

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .grading import wilson_ci, grade_citation

GRADE_COLORS = {
    "real-and-correct": "#2e7d32",
    "real-but-generic": "#f9a825",
    "real-but-wrong-family": "#e64a19",
    "no-citation": "#9e9e9e",
    "UNVERIFIED": "#455a64",
    "n/a-benign": "#cfd8dc",
}
GRADE_ORDER = list(GRADE_COLORS.keys())


def detect_benign_class(df):
    for name in df["true_class"].unique():
        if "benign" in str(name).lower():
            return name
    return None


def _short_grade(true_class, reference_id, benign_class):
    """grade_citation() returns a long UNVERIFIED string with explanation
    text; charts want the short category name."""
    g = grade_citation(true_class, reference_id, benign_class)
    return "UNVERIFIED" if g.startswith("UNVERIFIED") else g


def _bar_with_ci(ax, labels, stats, color, ylabel, title):
    """stats: list of (p, lo, hi, n) fractions in [0, 1]."""
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


def generate_condition_report(csv_path, out_dir, condition="rag_grounded",
                               manifest_path=None, benign_class=None,
                               sample_n=None, seed=42, export_inputs=True):
    """Filter csv_path down to `condition`, grade it, write charts + a CSV
    into out_dir, and (if manifest_path is given and export_inputs is True)
    copy each sample's PNG image and extract its raw pcap row-slice too.

    Returns the filtered, graded DataFrame.
    """
    if not os.path.isfile(csv_path):
        raise FileNotFoundError(f"Not found: {csv_path}")

    df = pd.read_csv(csv_path)
    df = df[df["classification"].astype(str).str.upper() != "ERROR"].copy()
    df = df[df["condition"] == condition].copy()
    if df.empty:
        raise ValueError(f"No {condition} rows found in {csv_path} -- nothing to process.")

    if sample_n is not None:
        available = len(df)
        n = min(sample_n, available)
        df = df.sample(n=n, random_state=seed).reset_index(drop=True)
        print(f"--sample-n {sample_n}: randomly picked {n} of {available} {condition} rows (seed={seed})")

    benign_class = benign_class or detect_benign_class(df)
    os.makedirs(out_dir, exist_ok=True)

    df["citation_grade"] = df.apply(
        lambda r: _short_grade(r["true_class"], r["reference_id"], benign_class), axis=1)
    df["correct"] = df["classification"].astype(str).str.strip() == df["true_class"].astype(str).str.strip()

    if manifest_path and os.path.isfile(manifest_path):
        manifest = pd.read_csv(manifest_path)[["sample_id", "source_file", "row_start", "row_end", "image_path"]]
        df = df.merge(manifest, on="sample_id", how="left")
        missing = int(df["source_file"].isna().sum())
        if missing:
            print(f"WARNING: {missing} sample(s) have no matching row in {manifest_path}.")
    elif manifest_path:
        print(f"WARNING: manifest not found at {manifest_path} -- skipping pcap/image input export.")
        export_inputs = False

    if export_inputs and "source_file" in df.columns:
        images_dir = os.path.join(out_dir, "images")
        slices_dir = os.path.join(out_dir, "pcap_slices")
        os.makedirs(images_dir, exist_ok=True)
        os.makedirs(slices_dir, exist_ok=True)

        copied_image_paths, pcap_slice_paths = [], []
        n_ok = 0
        for _, row in df.iterrows():
            sample_id = row["sample_id"]
            src_img, src_pcap = row.get("image_path"), row.get("source_file")
            if pd.isna(src_img) or pd.isna(src_pcap):
                copied_image_paths.append(None)
                pcap_slice_paths.append(None)
                continue

            dst_img = os.path.join(images_dir, f"{sample_id}.png")
            if os.path.isfile(src_img):
                shutil.copyfile(src_img, dst_img)
                copied_image_paths.append(dst_img)
            else:
                copied_image_paths.append(None)

            dst_slice = os.path.join(slices_dir, f"{sample_id}.csv")
            if os.path.isfile(src_pcap):
                # Read only the needed row range directly off disk rather than
                # loading (and caching) the whole source file -- across a
                # full multi-class run, source files can be large enough that
                # caching every distinct one in memory at once risks an OOM
                # kill. skiprows keeps the header (row 0) and skips the data
                # rows before row_start; nrows caps it to exactly the window.
                row_start, row_end = int(row["row_start"]), int(row["row_end"])
                sl = pd.read_csv(src_pcap, skiprows=range(1, row_start + 1), nrows=row_end - row_start)
                sl.to_csv(dst_slice, index=False)
                pcap_slice_paths.append(dst_slice)
                n_ok += 1
            else:
                pcap_slice_paths.append(None)

        df["copied_image_path"] = copied_image_paths
        df["pcap_slice_path"] = pcap_slice_paths
        print(f"Copied {n_ok} PNG image(s) + extracted {n_ok} pcap row-slice(s) into {out_dir}/")

    df.to_csv(os.path.join(out_dir, f"{condition}_results.csv"), index=False)

    # ---------- chart 1: citation quality ----------
    counts = df["citation_grade"].value_counts()
    grades_present = [g for g in GRADE_ORDER if g in counts.index]
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.bar(grades_present, [counts[g] for g in grades_present],
           color=[GRADE_COLORS[g] for g in grades_present])
    ax.set_ylabel("Number of samples")
    ax.set_title(f"{condition} citation quality (n={len(df)})")
    plt.setp(ax.get_xticklabels(), rotation=20, ha="right")
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "citation_quality.png"), dpi=150)
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
    fig.savefig(os.path.join(out_dir, "accuracy_overall.png"), dpi=150)
    plt.close(fig)

    # ---------- chart 3: per-class accuracy (only if >1 class) ----------
    classes = sorted(df["true_class"].unique())
    if len(classes) > 1:
        stats = []
        for cls in classes:
            g = df[df["true_class"] == cls]
            p, lo, hi = wilson_ci(int(g["correct"].sum()), len(g))
            stats.append((p, lo, hi, len(g)))
        fig, ax = plt.subplots(figsize=(max(7, len(classes) * 0.45), 5.5))
        _bar_with_ci(ax, classes, stats, "#2e74b5", "Classification accuracy (%)",
                     f"{condition} accuracy by class (Wilson 95% CI)")
        plt.setp(ax.get_xticklabels(), rotation=75, ha="right", fontsize=8)
        fig.tight_layout()
        fig.savefig(os.path.join(out_dir, "accuracy_by_class.png"), dpi=150)
        plt.close(fig)

    return df
