#!/usr/bin/env python3
"""
run_pipeline.py -- end-to-end entry point: build 2D and 3D visualizations
from the SAME sampled traffic windows, classify both with Claude (identical
prompt, only the image differs), and print/save an accuracy comparison.

This is the ONLY script in the project that spends real money -- both
render steps and the summary/report step are free.

Setup (once):
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=sk-ant-...

Usage:
    python3 scripts/run_pipeline.py --list-classes                          # free
    python3 scripts/run_pipeline.py --limit 5                               # cheap pilot
    python3 scripts/run_pipeline.py --classes Benign_Final,DDoS-TCP_Flood --limit 5
    python3 scripts/run_pipeline.py --limit 40 --samples-per-class 40       # submission-grade

Outputs (written to --out-dir, default ./results/):
    viz/2d/<class>/<sample_id>.png   -- 2D (4-panel) traffic visualizations
    viz/3d/<class>/<sample_id>.png   -- 3D (single-scene) traffic visualizations
    viz/manifest.csv                 -- sample metadata + both image paths
    harness_results.csv              -- Claude's classifications, one row per
                                         (sample, dimensionality)
    accuracy_2d_vs_3d.png            -- overall accuracy comparison chart
    accuracy_by_class_2d_vs_3d.png   -- per-class accuracy comparison chart
    summary.txt                      -- accuracy + paired-comparison tables
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from dimensionality_study.config import DEFAULT_DATA_DIR, DEFAULT_OUT_DIR, EMPIRICAL_COST_PER_CALL, MODEL, DIMENSIONALITIES
from dimensionality_study.data_loader import discover_classes
from dimensionality_study.build import build_visualizations
from dimensionality_study.claude_client import run_harness
from dimensionality_study.grading import score_and_summarize
from dimensionality_study.reporting import build_charts


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data-dir", default=DEFAULT_DATA_DIR,
                     help=f"directory containing one subfolder per class (default: {DEFAULT_DATA_DIR}, "
                          f"i.e. the sibling networksecurity project's already-downloaded dataset)")
    ap.add_argument("--out-dir", default=DEFAULT_OUT_DIR, help=f"default: {DEFAULT_OUT_DIR}")
    ap.add_argument("--classes", default=None,
                     help="comma-separated list of class subfolder names to include (default: all)")
    ap.add_argument("--limit", type=int, default=5,
                     help="samples per class sent to Claude (0 = all rendered). Default 5, matching "
                          "the sibling project's original pilot scale.")
    ap.add_argument("--samples-per-class", type=int, default=5,
                     help="total visualization samples to generate per class (should be >= --limit)")
    ap.add_argument("--model", default=MODEL, help=f"Claude model id (default: {MODEL})")
    ap.add_argument("--skip-llm", action="store_true",
                     help="only build the 2D/3D visualizations and manifest, no API calls")
    ap.add_argument("--list-classes", action="store_true",
                     help="just print discovered classes and file counts, then exit")
    ap.add_argument("--no-resume", action="store_true")
    ap.add_argument("--yes", "-y", action="store_true",
                     help="skip the cost-estimate confirmation pause")
    args = ap.parse_args()

    only_classes = set(args.classes.split(",")) if args.classes else None
    class_files = discover_classes(args.data_dir, only_classes)

    print(f"Discovered {len(class_files)} classes under {args.data_dir}:")
    for name, files in class_files.items():
        print(f"  {name}: {len(files)} file(s)")

    if args.list_classes:
        return

    if not args.skip_llm:
        est_calls = (sum(min(args.limit, args.samples_per_class) if args.limit > 0 else args.samples_per_class
                          for _ in class_files) * len(DIMENSIONALITIES))
        est_cost = est_calls * EMPIRICAL_COST_PER_CALL
        print(f"\nEstimated Claude API calls for this run: ~{est_calls} "
              f"({len(class_files)} classes x up to {args.limit or args.samples_per_class} samples "
              f"x {len(DIMENSIONALITIES)} dimensionalities).")
        print(f"Estimated cost: ~${est_cost:.2f} (based on an observed ~${EMPIRICAL_COST_PER_CALL}/call "
              f"from the sibling project's pilot; this project's images/prompts are similar in size, "
              f"but not yet independently measured).")
        if not args.yes:
            print("Ctrl-C now if that's more than you want to spend, or pass --yes next time to skip this pause.")

    os.makedirs(args.out_dir, exist_ok=True)
    print("\nBuilding 2D and 3D visualizations from the same sampled windows...")
    manifest = build_visualizations(class_files, args.samples_per_class, out_dir=args.out_dir)

    class_names = sorted(class_files.keys())
    harness_results = None
    if not args.skip_llm:
        print("\nRunning Claude harness (this calls the Anthropic API and will incur cost)...")
        harness_results = run_harness(manifest, args.limit, class_names, out_dir=args.out_dir,
                                       resume=not args.no_resume, model=args.model)
    else:
        print("\n--skip-llm set: skipping Claude harness entirely.")

    if harness_results is not None:
        print("\n" + "=" * 60)
        score_and_summarize(harness_results, out_dir=args.out_dir)
        build_charts(harness_results, out_dir=args.out_dir)
        print(f"\nCharts written: {args.out_dir}/accuracy_2d_vs_3d.png, "
              f"{args.out_dir}/accuracy_by_class_2d_vs_3d.png")

    print(f"\nAll outputs saved under ./{args.out_dir}/")


if __name__ == "__main__":
    main()
