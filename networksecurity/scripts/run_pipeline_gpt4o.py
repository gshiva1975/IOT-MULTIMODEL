#!/usr/bin/env python3
"""
run_pipeline_gpt4o.py -- run the identical 3-condition citation-grounding
experiment against GPT-4o instead of Claude, for a cross-model comparison.

By default this REUSES the existing results/viz/manifest.csv that
run_pipeline.py already produced -- i.e. the exact same rendered traffic
images Claude was shown -- so the two models' results are directly
comparable, not drawn from a fresh independent sample. Run run_pipeline.py
first (even with --skip-llm, which costs nothing) if you don't have a
manifest yet.

Setup (once):
    pip install openai
    export OPENAI_API_KEY=sk-...

Usage:
    # 1. Always sanity-check with ONE call first -- confirms the API key,
    #    billing, and model access all work before you spend real money:
    python3 scripts/run_pipeline_gpt4o.py --probe

    # 2. Match whatever --limit you used for the Claude run, e.g. 5/class:
    python3 scripts/run_pipeline_gpt4o.py --limit 5

    # Cheaper pilot with gpt-4o-mini instead of gpt-4o:
    python3 scripts/run_pipeline_gpt4o.py --limit 5 --model gpt-4o-mini

Outputs (written into --out-dir, alongside the Claude run's files):
    harness_results_gpt4o.csv   -- GPT-4o's classifications + citations (3 conditions)
    summary_gpt4o.txt           -- accuracy + citation-quality tables for this model

This script does NOT re-run the non-LLM baselines (z-score / Isolation
Forest) -- those are model-independent and already computed by
run_pipeline.py; reuse --out-dir/baseline_results.csv for that comparison.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

import pandas as pd

from networksecurity.config import DEFAULT_OUT_DIR
from networksecurity.data_loader import find_benign_class
from networksecurity.corpus import CVE_CORPUS
from networksecurity.grading import wilson_ci, fmt_ci, grade_citation
from networksecurity import openai_client


def summarize_gpt4o_results(harness_results, benign_class, out_dir):
    """Same accuracy / citation-quality tables as grading.score_and_summarize(),
    but labeled for GPT-4o rather than hard-coded to say 'Claude', and written
    to summary_gpt4o.txt instead of summary.txt so it never collides with the
    Claude run's summary."""
    lines = []

    def log(s=""):
        print(s)
        lines.append(s)

    harness_results = harness_results.copy()
    harness_results["correct"] = (harness_results["classification"].str.strip()
                                   == harness_results["true_class"].str.strip())
    log("=== GPT-4o classification accuracy by condition (Wilson 95% CI) ===")
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

    with open(os.path.join(out_dir, "summary_gpt4o.txt"), "w") as f:
        f.write("\n".join(lines))
    return lines


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", default=None,
                     help="path to an existing viz manifest CSV (default: <out-dir>/viz/manifest.csv, "
                          "produced by run_pipeline.py) -- reuses the SAME sample images the Claude "
                          "harness classified, for a like-for-like comparison.")
    ap.add_argument("--out-dir", default=DEFAULT_OUT_DIR,
                     help=f"where the manifest lives and where GPT-4o's results get written "
                          f"(default: {DEFAULT_OUT_DIR}, same folder run_pipeline.py used)")
    ap.add_argument("--classes", default=None,
                     help="comma-separated list of class names to include (default: all in manifest)")
    ap.add_argument("--benign-class", default=None,
                     help="exact class name for normal traffic (default: auto-detect 'benign' in name)")
    ap.add_argument("--limit", type=int, default=5,
                     help="GPT-4o samples per class (0 = all in manifest). Default 5 -- match "
                          "whatever --limit you used for the Claude run for a fair comparison.")
    ap.add_argument("--model", default="gpt-4o",
                     help="OpenAI model id (default: gpt-4o). Cheaper alternative: gpt-4o-mini.")
    ap.add_argument("--probe", action="store_true",
                     help="make ONE test call (first sample, naive condition) and print the full "
                          "response or full error diagnostics, then exit -- always run this before "
                          "a full (paid) run.")
    ap.add_argument("--no-resume", action="store_true",
                     help="by default, a rerun with the same arguments skips already-completed "
                          "calls and retries only ERROR rows. Pass this to force a clean run.")
    ap.add_argument("--yes", "-y", action="store_true",
                     help="skip the cost-estimate confirmation pause and run immediately")
    args = ap.parse_args()

    manifest_path = args.manifest or os.path.join(args.out_dir, "viz", "manifest.csv")
    if not os.path.isfile(manifest_path):
        sys.exit(f"Manifest not found: {manifest_path}\n"
                  f"Run scripts/run_pipeline.py first (add --skip-llm if you just want the "
                  f"visualizations and not another Claude bill) to generate it.")

    manifest = pd.read_csv(manifest_path)
    if args.classes:
        only_classes = set(args.classes.split(","))
        manifest = manifest[manifest["true_class"].isin(only_classes)]
    class_names = sorted(manifest["true_class"].unique().tolist())
    benign_class = args.benign_class or find_benign_class({c: [] for c in class_names})

    print(f"Reusing existing manifest: {manifest_path} ({len(manifest)} samples, "
          f"{len(class_names)} classes)")
    if benign_class:
        print(f"Using '{benign_class}' as the benign/normal-traffic class for citation grading.")
    else:
        print("WARNING: could not auto-detect a benign class -- pass --benign-class explicitly.")

    if args.probe:
        openai_client.probe(manifest, class_names, args.model)
        return

    est_calls = (sum(args.limit for _ in class_names) if args.limit > 0 else len(manifest)) * 3
    est_cost = openai_client.estimate_cost(est_calls, args.model)
    print(f"\nEstimated OpenAI API calls for this run: ~{est_calls} "
          f"({len(class_names)} classes x up to {args.limit or 'all'} samples x 3 conditions).")
    print(f"Estimated cost: ~${est_cost:.2f} using {args.model} (rough estimate based on the "
          f"Claude pilot's observed token counts; actual cost depends on image size and response "
          f"length -- check https://platform.openai.com/usage after running).")
    if not args.yes:
        print("Ctrl-C now if that's more than you want to spend, or pass --yes next time to skip "
              "this pause. Run with --probe first if you haven't yet.")

    os.makedirs(args.out_dir, exist_ok=True)
    with open(os.path.join(args.out_dir, "cve_corpus.json"), "w") as f:
        json.dump(CVE_CORPUS, f, indent=2)

    print(f"\nRunning GPT-4o harness ({args.model}, this calls the OpenAI API and will incur cost)...")
    harness_results = openai_client.run_harness(manifest, args.limit, class_names, args.out_dir,
                                                  model=args.model, resume=not args.no_resume)

    print("\n" + "=" * 60)
    summarize_gpt4o_results(harness_results, benign_class, args.out_dir)
    print(f"\nAll GPT-4o outputs saved under ./{args.out_dir}/ "
          f"(harness_results_gpt4o.csv, summary_gpt4o.txt)")
    print("Compare against harness_results.csv (Claude) using generate_rag_report.py's grading "
          "logic -- both files share identical column names/semantics.")


if __name__ == "__main__":
    main()
