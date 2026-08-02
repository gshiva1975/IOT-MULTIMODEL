#!/usr/bin/env python3
"""
generate_rag_report.py -- filter harness_results.csv down to one condition
(rag_grounded by default), chart it, and export the exact inputs (traffic
images + raw pcap row-slices) each sample used.

Costs nothing -- this is pure local post-processing of data run_pipeline.py
already produced and paid for. Safe to rerun as many times as you like.

Usage:
    python3 scripts/generate_rag_report.py
    python3 scripts/generate_rag_report.py --condition naive
    python3 scripts/generate_rag_report.py --sample-n 10
    python3 scripts/generate_rag_report.py --sample-n 10 --seed 7
    python3 scripts/generate_rag_report.py --csv results/harness_results.csv \\
        --manifest results/viz/manifest.csv --out results/rag_grounded

Outputs (under --out, default results/rag_grounded/):
    rag_grounded_results.csv    -- the filtered rows + citation_grade, joined with manifest paths
    citation_quality.png        -- bar chart of citation_grade counts
    accuracy_overall.png        -- overall classification accuracy, Wilson 95% CI
    accuracy_by_class.png       -- per-class accuracy, Wilson 95% CI (only if >1 class present)
    images/<sample_id>.png      -- copy of the exact traffic image Claude was shown, per sample
    pcap_slices/<sample_id>.csv -- the exact raw rows that image was built from, per sample
"""

import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "src"))

from networksecurity.config import DEFAULT_OUT_DIR
from networksecurity.reporting import generate_condition_report


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv", default=os.path.join(DEFAULT_OUT_DIR, "harness_results.csv"),
                     help="path to harness_results.csv (default: results/harness_results.csv)")
    ap.add_argument("--manifest", default=os.path.join(DEFAULT_OUT_DIR, "viz", "manifest.csv"),
                     help="path to the viz manifest CSV (default: results/viz/manifest.csv)")
    ap.add_argument("--out", default=os.path.join(DEFAULT_OUT_DIR, "rag_grounded"),
                     help="folder to write the filtered CSV + charts + inputs to")
    ap.add_argument("--condition", default="rag_grounded",
                     choices=["naive", "cve_text_grounded", "rag_grounded"],
                     help="which prompting condition to isolate (default: rag_grounded)")
    ap.add_argument("--benign-class", default=None,
                     help="exact true_class value for normal traffic (default: auto-detect)")
    ap.add_argument("--sample-n", type=int, default=None,
                     help="randomly pick this many rows to process instead of all of them")
    ap.add_argument("--seed", type=int, default=42, help="random seed for --sample-n (default: 42)")
    ap.add_argument("--no-inputs", action="store_true",
                     help="skip copying PNG images and extracting pcap row-slices -- charts + CSV only")
    args = ap.parse_args()

    try:
        df = generate_condition_report(
            csv_path=args.csv, out_dir=args.out, condition=args.condition,
            manifest_path=args.manifest, benign_class=args.benign_class,
            sample_n=args.sample_n, seed=args.seed, export_inputs=not args.no_inputs,
        )
    except (FileNotFoundError, ValueError) as e:
        sys.exit(str(e))

    print(f"Processed {len(df)} {args.condition} rows -> {args.out}/")


if __name__ == "__main__":
    main()
