"""
openai_client.py -- the OpenAI-model twin of claude_client.py, for running the
identical 3-condition experiment against a second multimodal LLM (GPT-4o by
default) for a cross-model comparison.

Deliberately reuses everything provider-agnostic from the rest of the package
(corpus.py, prompting.py, grading.py) unchanged -- only the model-calling code
differs from claude_client.py. This mirrors the proven run_experiment_openai.py
harness from the original research script (same retry/backoff, --probe
single-call sanity check, and resume semantics), ported onto this package so
it can point at the exact same manifest.csv / rendered images the Claude run
already produced -- a like-for-like comparison, not a fresh independent draw.

Results are written to a SEPARATE file, harness_results_gpt4o.csv, in the same
--out-dir as the Claude run, so they sit side by side without ever colliding
with harness_results.csv.

Setup (once):
    pip install openai
    export OPENAI_API_KEY=sk-...
"""

import base64
import csv
import os
import sys
import time

import pandas as pd

from .prompting import build_prompt, parse_response

RESULT_COLUMNS = [
    "sample_id", "true_class", "condition", "classification", "reference_id",
    "justification", "input_tokens", "output_tokens", "raw_response",
]

# Pricing as of mid-2026 (openai.com/api/pricing): gpt-4o $2.50/$10.00 per 1M
# input/output tokens; gpt-4o-mini $0.15/$0.60 -- a much cheaper pilot option.
COST_PER_1M = {
    "gpt-4o": (2.50, 10.00),
    "gpt-4o-mini": (0.15, 0.60),
}
# Observed on the Claude harness's pilot run (avg ~1993 input + 216 output
# tokens/call). OpenAI's image-tiling token accounting differs slightly from
# Anthropic's, but this is a reasonable estimate for the pre-run cost printout.
EST_INPUT_TOKENS_PER_CALL = 2000
EST_OUTPUT_TOKENS_PER_CALL = 220


def estimate_cost(n_calls, model):
    in_price, out_price = COST_PER_1M.get(model, COST_PER_1M["gpt-4o"])
    return n_calls * (EST_INPUT_TOKENS_PER_CALL / 1e6 * in_price
                       + EST_OUTPUT_TOKENS_PER_CALL / 1e6 * out_price)


def image_data_uri(path):
    with open(path, "rb") as f:
        data = base64.standard_b64encode(f.read()).decode("utf-8")
    return f"data:image/png;base64,{data}"


def describe_exception(e):
    """openai's SDK errors usually have a readable str(e), but this also
    surfaces HTTP status/body when present (rate limits, invalid key, model
    access not enabled on this account)."""
    parts = [f"{type(e).__name__}"]
    msg = str(e).strip()
    if msg:
        parts.append(msg)
    resp = getattr(e, "response", None)
    if resp is not None:
        try:
            status = getattr(resp, "status_code", None)
            body = getattr(resp, "text", "") or ""
            if status is not None:
                parts.append(f"HTTP {status}")
            if body.strip():
                parts.append(body.strip()[:500])
        except Exception:
            pass
    return " | ".join(p for p in parts if p)


def build_client():
    try:
        from openai import OpenAI
    except ImportError:
        sys.exit("Missing dependency. Run: pip install openai")
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        sys.exit("Set OPENAI_API_KEY in your environment first "
                  "(https://platform.openai.com/api-keys).")
    return OpenAI(api_key=api_key)


def call_openai_model(client, model, prompt, img_uri, max_tokens=400, retries=4):
    """Call an OpenAI vision model via chat.completions, with retry/backoff
    for transient rate-limit / server errors."""
    last_err = None
    for attempt in range(retries):
        try:
            completion = client.chat.completions.create(
                model=model,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": img_uri}},
                    ],
                }],
                max_tokens=max_tokens,
            )
            return completion.choices[0].message.content, completion.usage
        except Exception as e:
            last_err = e
            wait = min(30, 2 ** attempt * 3)
            print(f"    (retry {attempt + 1}/{retries} after error: "
                  f"{describe_exception(e)}; waiting {wait}s)")
            time.sleep(wait)
    raise RuntimeError(f"Exhausted retries calling {model}: {describe_exception(last_err)}")


def load_resumable_results(path):
    """Same resume semantics as claude_client.py: only rows with a real,
    non-ERROR classification count as done; ERROR rows (quota/refusal/rate
    limit/etc., none of which produced a usable result) are dropped and
    retried on the next run."""
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


def probe(manifest, class_names, model):
    """Make ONE test call (first sample in the manifest, naive condition) and
    print the full response or full error diagnostics, then return. Always
    run this before a full (paid) run."""
    try:
        import openai  # noqa: F401
    except ImportError:
        sys.exit("Missing dependency. Run: pip install openai")
    row = manifest.iloc[0]
    print(f"\n--probe: sending ONE call for sample_id={row['sample_id']} "
          f"(true_class={row['true_class']}), condition=naive, model={model} ...")
    client = build_client()
    prompt = build_prompt("naive", class_names)
    try:
        img_uri = image_data_uri(row["image_path"])
        text, usage = call_openai_model(client, model, prompt, img_uri, retries=1)
        print("\n--probe SUCCEEDED. Raw response:\n" + "-" * 40)
        print(text)
        print("-" * 40)
        print(f"Tokens: input={getattr(usage, 'prompt_tokens', '?')} "
              f"output={getattr(usage, 'completion_tokens', '?')}")
        print("\nThis model works -- rerun without --probe to do the full run.")
    except Exception as e:
        print("\n--probe FAILED.")
        print("Diagnostics: " + describe_exception(e))
        print("\nCommon causes: OPENAI_API_KEY not set/invalid, no billing/payment method on "
              "the account, or the account doesn't have access to this model -- check "
              "https://platform.openai.com/settings/organization/billing/overview")


def run_harness(manifest, limit, class_names, out_dir, model="gpt-4o", resume=True):
    try:
        import openai  # noqa: F401
    except ImportError:
        sys.exit("Missing dependency. Run: pip install openai")

    client = build_client()

    run_manifest = manifest
    if limit > 0:
        run_manifest = manifest.groupby("true_class", group_keys=False).head(limit)

    conditions = ["naive", "cve_text_grounded", "rag_grounded"]
    total_calls = len(run_manifest) * len(conditions)

    out_path = os.path.join(out_dir, "harness_results_gpt4o.csv")
    kept_rows, done_keys = load_resumable_results(out_path) if resume else ([], set())
    if done_keys:
        print(f"--resume: found {len(done_keys)} already-completed (sample, condition) calls in "
              f"{out_path} -- skipping those, retrying any stale ERROR rows.")
        pd.DataFrame(kept_rows, columns=RESULT_COLUMNS).to_csv(out_path, index=False)

    remaining = total_calls - len(done_keys)
    print(f"Running {len(run_manifest)} samples x {len(conditions)} conditions = {total_calls} "
          f"OpenAI API calls ({model}, {remaining} remaining) across {len(class_names)} classes: "
          f"{', '.join(class_names)}")

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
            img_uri = None
            for condition in conditions:
                key = (row["sample_id"], condition)
                if key in done_keys:
                    continue
                if img_uri is None:
                    img_uri = image_data_uri(row["image_path"])
                prompt = build_prompt(condition, class_names)
                try:
                    text, usage = call_openai_model(client, model, prompt, img_uri)
                    parsed = parse_response(text)
                    result_row = {
                        "sample_id": row["sample_id"], "true_class": row["true_class"],
                        "condition": condition, "classification": parsed["classification"],
                        "reference_id": parsed["reference_id"], "justification": parsed["justification"],
                        "input_tokens": getattr(usage, "prompt_tokens", 0),
                        "output_tokens": getattr(usage, "completion_tokens", 0),
                        "raw_response": (text or "").replace("\n", " | "),
                    }
                except Exception as e:
                    sid = row.get("sample_id", "UNKNOWN_SAMPLE")
                    tc = row.get("true_class", "UNKNOWN_CLASS")
                    diag = describe_exception(e)
                    print(f"ERROR on {sid} / {condition}: {diag}")
                    result_row = {"sample_id": sid, "true_class": tc,
                                   "condition": condition, "classification": "ERROR", "reference_id": "",
                                   "justification": diag, "input_tokens": 0, "output_tokens": 0,
                                   "raw_response": ""}
                rows.append(result_row)
                writer.writerow(result_row)
                csv_file.flush()
                done += 1
                if done % 10 == 0:
                    print(f"  {done}/{total_calls} calls done")
    finally:
        csv_file.close()

    return pd.DataFrame(rows, columns=RESULT_COLUMNS)
