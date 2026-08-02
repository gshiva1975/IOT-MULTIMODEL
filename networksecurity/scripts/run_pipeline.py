#!/usr/bin/env python3
"""
run_pipeline.py -- end-to-end entry point: build traffic visualizations,
classify them with Claude under 3 prompting conditions, run non-LLM
baselines for comparison, and print/save a scored summary.

This is the ONLY script in the project that spends real money -- every
other script (generate_rag_report.py) just re-processes data this one
already produced.

Setup (once):
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=sk-ant-...

Usage:
    python3 scripts/run_pipeline.py --data-dir data/CSV --list-classes
    python3 scripts/run_pipeline.py --data-dir data/CSV --limit 10             # cheap pilot
    python3 scripts/run_pipeline.py --data-dir data/CSV --limit 0              # full run
    python3 scripts/run_pipeline.py --data-dir data/CSV --skip-llm             # baselines only, no API cost
    python3 scripts/run_pipeline.py --data-dir data/CSV --classes Benign,DDoS-TCP_Flood
    python3 scripts/run_pipeline.py --data-dir data/CSV --limit 40 --samples-per-class 40   # submission-grade run

Outputs (written to --out-dir, default ./results/):
    viz/<class>/<sample_id>.png   -- the traffic visualizations
    viz/manifest.csv              -- sample metadata: source file/rows each came from
    harness_results.csv           -- Claude's classifications + citations (3 conditions)
    baseline_results.csv          -- z-score / Isolation Forest flags
    summary.txt                   -- accuracy + citation-quality tables, printed and saved
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from networksecurity.config import DEFAULT_DATA_DIR, DEFAULT_OUT_DIR, EMPIRICAL_COST_PER_CALL, MODEL
from networksecurity.data_loader import discover_classes, find_benign_class
from networksecurity.visualization import build_visualizations
from networksecurity.claude_client import run_harness
from networksecurity.baselines import run_baselines
from networksecurity.grading import score_and_summarize


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data-dir", default=DEFAULT_DATA_DIR,
                     help=f"directory containing one subfolder per class, each full of CSV part "
                          f"files (default: {DEFAULT_DATA_DIR})")
    ap.add_argument("--out-dir", default=DEFAULT_OUT_DIR,
                     help=f"where to write viz/, harness_results.csv, etc. (default: {DEFAULT_OUT_DIR})")
    ap.add_argument("--classes", default=None,
                     help="comma-separated list of class subfolder names to include (default: all)")
    ap.add_argument("--benign-class", default=None,
                     help="exact class name to treat as normal traffic for baseline training "
                          "(default: auto-detect by matching 'benign' in the folder name)")
    ap.add_argument("--limit", type=int, default=10,
                     help="Claude samples per class (0 = all). Default 10 for a cheap pilot.")
    ap.add_argument("--samples-per-class", type=int, default=40,
                     help="total visualization samples to generate per class (should be >= --limit)")
    ap.add_argument("--model", default=MODEL, help=f"Claude model id (default: {MODEL})")
    ap.add_argument("--skip-llm", action="store_true",
                     help="only run the non-LLM baselines (no API key needed, no cost)")
    ap.add_argument("--list-classes", action="store_true",
                     help="just print discovered classes and file counts, then exit")
    ap.add_argument("--no-resume", action="store_true",
                     help="by default, a rerun with the SAME arguments skips already-completed "
                          "calls and retries only ERROR rows. Pass this to force a clean run.")
    ap.add_argument("--yes", "-y", action="store_true",
                     help="skip the cost-estimate confirmation pause and run immediately")
    args = ap.parse_args()

    only_classes = set(args.classes.split(",")) if args.classes else None
    class_files = discover_classes(args.data_dir, only_classes)

    print(f"Discovered {len(class_files)} classes under {args.data_dir}:")
    for name, files in class_files.items():
        print(f"  {name}: {len(files)} file(s)")

    if args.list_classes:
        return

    benign_class = args.benign_class or find_benign_class(class_files)
    if benign_class:
        print(f"\nUsing '{benign_class}' as the normal-traffic class for baseline training.")
    else:
        print("\nWARNING: could not auto-detect a benign class (no folder name contains 'benign'). "
              "Pass --benign-class explicitly, or baselines will be skipped.")

    if not args.skip_llm:
        est_calls = (sum(min(args.limit, args.samples_per_class) if args.limit > 0 else args.samples_per_class
                          for _ in class_files) * 3)
        est_cost = est_calls * EMPIRICAL_COST_PER_CALL
        print(f"\nEstimated Claude API calls for this run: ~{est_calls} "
              f"({len(class_files)} classes x up to {args.limit or args.samples_per_class} samples x 3 conditions).")
        print(f"Estimated cost: ~${est_cost:.2f} (based on observed ~${EMPIRICAL_COST_PER_CALL}/call from a "
              f"prior pilot; actual cost depends on image size and response length).")
        if not args.yes:
            print("Ctrl-C now if that's more than you want to spend, or pass --yes next time to skip this pause.")

    os.makedirs(args.out_dir, exist_ok=True)
    import json
    from networksecurity.corpus import CVE_CORPUS
    with open(os.path.join(args.out_dir, "cve_corpus.json"), "w") as f:
        json.dump(CVE_CORPUS, f, indent=2)

    print("\nBuilding visualizations...")
    manifest = build_visualizations(class_files, args.samples_per_class, out_dir=args.out_dir)

    class_names = sorted(class_files.keys())
    harness_results = None
    if not args.skip_llm:
        print("\nRunning Claude harness (this calls the Anthropic API and will incur cost)...")
        harness_results = run_harness(manifest, args.limit, class_names, out_dir=args.out_dir,
                                       resume=not args.no_resume, model=args.model)
    else:
        print("\n--skip-llm set: skipping Claude harness entirely.")

    print("\nRunning non-LLM baseline detectors (z-score, Isolation Forest)...")
    baseline_results = run_baselines(manifest, class_files, benign_class, out_dir=args.out_dir)

    print("\n" + "=" * 60)
    score_and_summarize(harness_results, baseline_results, benign_class, out_dir=args.out_dir)
    print(f"\nAll outputs saved under ./{args.out_dir}/")


if __name__ == "__main__":
    main()
