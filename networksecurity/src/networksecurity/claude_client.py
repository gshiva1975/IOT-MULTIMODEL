"""
claude_client.py -- the only module in this project that actually calls the
Anthropic API. Everything else (corpus, prompting, grading, charts) is pure
and network-free, which is deliberate: it makes the rest of the codebase
testable without an API key, and makes it obvious where a real network call
and real cost happen.

Resume behavior: results are written incrementally, one row per (sample,
condition) API call, to harness_results.csv. A rerun with the same
arguments automatically skips already-completed calls and retries only
ERROR rows, so an interruption (billing, rate limit, Ctrl-C, network drop)
never costs you a redo of work you already paid for. Pass resume=False to
force a clean run instead.
"""

import base64
import csv
import os
import sys

import pandas as pd

from .config import CONDITIONS, RESULT_COLUMNS, MODEL, DEFAULT_OUT_DIR
from .prompting import build_prompt, parse_response


def image_block(path):
    with open(path, "rb") as f:
        data = base64.standard_b64encode(f.read()).decode("utf-8")
    return {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": data}}


def load_resumable_results(path):
    """Only rows with a real, non-ERROR classification count as 'done' --
    ERROR rows (billing/rate-limit/network failures, which never actually
    got billed since the call didn't complete) are treated as not-yet-done
    and will be retried. Returns (kept_rows, done_keys)."""
    if not os.path.isfile(path):
        return [], set()
    existing = pd.read_csv(path)
    kept_rows, done_keys = [], set()
    for r in existing.to_dict("records"):
        cls = str(r.get("classification", "")).strip()
        if cls and cls.upper() not in ("ERROR", "NAN", ""):
            kept_rows.append(r)
            done_keys.add((r["sample_id"], r["condition"]))
    return kept_rows, done_keys


def run_harness(manifest, limit, class_names, out_dir=DEFAULT_OUT_DIR, resume=True, model=MODEL):
    try:
        import anthropic
    except ImportError:
        sys.exit("Missing dependency. Run: pip install anthropic")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        sys.exit("Set ANTHROPIC_API_KEY in your environment first.")
    client = anthropic.Anthropic(api_key=api_key)

    run_manifest = manifest
    if limit > 0:
        run_manifest = manifest.groupby("true_class", group_keys=False).head(limit)

    total_calls = len(run_manifest) * len(CONDITIONS)

    out_path = os.path.join(out_dir, "harness_results.csv")
    kept_rows, done_keys = load_resumable_results(out_path) if resume else ([], set())
    if done_keys:
        print(f"--resume: found {len(done_keys)} already-completed (sample, condition) calls in "
              f"{out_path} -- these will be skipped, and any stale ERROR rows for retried calls "
              f"have been dropped from the rewritten file.")
        pd.DataFrame(kept_rows, columns=RESULT_COLUMNS).to_csv(out_path, index=False)

    remaining = total_calls - len(done_keys)
    print(f"Running {len(run_manifest)} samples x {len(CONDITIONS)} conditions = {total_calls} API "
          f"calls ({remaining} remaining) across {len(class_names)} classes: {', '.join(class_names)}")

    file_exists = os.path.isfile(out_path)
    csv_file = open(out_path, "a", newline="")
    writer = csv.DictWriter(csv_file, fieldnames=RESULT_COLUMNS)
    if not file_exists:
        writer.writeheader()
        csv_file.flush()

    rows = list(kept_rows)
    done = len(done_keys)
    try:
        for _, row in run_manifest.iterrows():
            img = None
            for condition in CONDITIONS:
                key = (row["sample_id"], condition)
                if key in done_keys:
                    continue
                if img is None:
                    img = image_block(row["image_path"])
                prompt = build_prompt(condition, class_names)
                try:
                    resp = client.messages.create(
                        model=model, max_tokens=400,
                        messages=[{"role": "user", "content": [img, {"type": "text", "text": prompt}]}],
                    )
                    text_blocks = [b.text for b in resp.content if getattr(b, "type", None) == "text"]
                    if not text_blocks:
                        raise RuntimeError(f"No text block in response (content types: "
                                            f"{[getattr(b, 'type', type(b)) for b in resp.content]})")
                    text = "".join(text_blocks)
                    parsed = parse_response(text)
                    result_row = {
                        "sample_id": row["sample_id"], "true_class": row["true_class"],
                        "condition": condition, "classification": parsed["classification"],
                        "reference_id": parsed["reference_id"], "justification": parsed["justification"],
                        "input_tokens": resp.usage.input_tokens, "output_tokens": resp.usage.output_tokens,
                        "raw_response": text,
                    }
                except Exception as e:
                    result_row = {
                        "sample_id": row["sample_id"], "true_class": row["true_class"],
                        "condition": condition, "classification": "ERROR", "reference_id": None,
                        "justification": str(e), "input_tokens": None, "output_tokens": None,
                        "raw_response": None,
                    }
                rows.append(result_row)
                writer.writerow(result_row)
                csv_file.flush()
                done += 1
                if done % 10 == 0:
                    print(f"  {done}/{total_calls} calls done")
    finally:
        csv_file.close()

    return pd.DataFrame(rows, columns=RESULT_COLUMNS)
