# dimensionality_study

Does the *dimensionality* of a traffic visualization change how well a multimodal
LLM classifies it -- holding everything else (the underlying data, the classes,
the model, the prompt) constant?

This is a focused follow-on to the sibling [`../networksecurity`](../networksecurity)
project. That project varies the *prompt* (naive / text-grounded / RAG-grounded) and
holds the image constant, to study citation hallucination. This project does the
opposite: it holds the prompt constant and varies the *image* -- a 2D multi-panel
time series vs. a single fused 3D scene of the same underlying features -- to study
whether visual encoding itself affects classification accuracy.

## The two conditions

Both conditions are rendered from the **exact same sampled traffic windows** (same
`row_start`/`row_end` in the same source file), so any accuracy difference measured
is attributable to the visualization, not to sampling noise. See `build.py`'s
docstring -- this shared-sampling guarantee is the core of the experiment design.

- **2D** (`visualization_2d.py`): four stacked 2D panels -- packet rate, TCP flag
  composition, protocol mix (stacked area), packet size statistics. Identical
  rendering to the citation-grounding study, ported unchanged.
- **3D** (`visualization_3d.py`): the same four feature groups fused into one 3D
  scene -- x/y/z axes are (time, packet rate, avg packet size), with TCP-flag
  intensity as point color and dominant-protocol share as point size. Includes a
  floor projection and connecting trajectory line, a standard mitigation for 3D
  scatter-plot occlusion, so the 3D condition is a fair, competently-rendered
  comparison rather than a strawman.

## Quick start

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...

python3 scripts/run_pipeline.py --list-classes                # free, no API call
python3 scripts/run_pipeline.py --limit 5                     # cheap pilot, ~$0.06/class x 2 dims
```

By default `--data-dir` points at `../networksecurity/data/CSV` -- the dataset
already downloaded for the sibling project -- so you don't need a second multi-GB
copy of CIC-IoT-2023. Override with `--data-dir` if you've moved things.

### Example: two-class pilot

```bash
python3 scripts/run_pipeline.py --classes Benign_Final,DDoS-TCP_Flood --limit 5
```

That's 2 classes x 5 samples x 2 dimensionalities = 20 API calls, a few cents.

## Cost estimates

Same per-call cost as the sibling project's Claude pilot (~$0.0061/call, not yet
independently re-measured for this project's shorter prompt and different image
sizes -- treat the printed estimate as a rough guide, and check
`results/harness_results.csv`'s `input_tokens`/`output_tokens` columns after your
first run for a real number).

| Run | API calls | Est. cost |
|---|---|---|
| `--list-classes` / `--skip-llm` | 0 | $0 |
| `--limit 5` on 2 classes | 20 | ~$0.12 |
| `--limit 5` on all 34 classes | 340 | ~$2.07 |
| `--limit 40` on all 34 classes (submission-grade) | 2,720 | ~$16.60 |

## Outputs

```
results/
  viz/2d/<class>/<sample_id>.png   -- 2D visualizations
  viz/3d/<class>/<sample_id>.png   -- 3D visualizations
  viz/manifest.csv                 -- sample metadata + both image paths
  harness_results.csv              -- one row per (sample, dimensionality)
  accuracy_2d_vs_3d.png            -- overall accuracy comparison chart
  accuracy_by_class_2d_vs_3d.png   -- per-class accuracy comparison chart
  summary.txt                      -- accuracy + paired-comparison tables
```

The paired comparison in `summary.txt` (and computed in `grading.py`) is the more
statistically informative view at small n: for each sample where both
dimensionalities completed, did 2D and 3D agree, and when they disagreed, which one
was actually correct? This controls for per-sample difficulty in a way that
comparing raw 2D-accuracy vs. raw 3D-accuracy across the whole set does not.

## Project layout

```
dimensionality_study/
  README.md
  requirements.txt / requirements-dev.txt
  src/dimensionality_study/
    config.py             -- constants (model id, feature columns, data dir)
    data_loader.py         -- discover classes/files (ported from networksecurity)
    sampling.py             -- picks which windows become samples (shared by both renderers)
    build.py                 -- ties sampling to both renderers, writes the shared manifest
    visualization_2d.py       -- 4-panel 2D renderer (ported unchanged)
    visualization_3d.py        -- 3D scene renderer (new)
    prompting.py                 -- ONE prompt, held constant across both conditions
    claude_client.py              -- THE ONLY MODULE THAT CALLS THE API
    grading.py                     -- Wilson 95% CI + paired comparison
    reporting.py                    -- comparison charts
  scripts/
    run_pipeline.py                  -- CLI: full experiment (costs money)
  tests/                              -- unit tests, no API key or network needed
```

## Testing

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

20 tests, all pure-function -- no API key, no network, no sample data needed. Covers
Wilson CI bounds, prompt construction, response parsing, window-sampling edge cases,
and that both renderers produce valid matplotlib figures from synthetic data.

## Known simplifications

- Citation grounding is deliberately out of scope here -- this project only measures
  classification accuracy, to isolate the visualization-dimensionality question from
  the citation-hallucination question the sibling project already covers. If you
  want both axes crossed (2D/3D x naive/text-grounded/rag-grounded), that's a
  natural but more expensive extension: 6 conditions/sample instead of 2.
- The specific 3D encoding (time/rate/packet-size axes, flag-intensity color,
  protocol-share size) is one reasonable design, not the only one -- a different
  axis/encoding choice could plausibly change the result. Worth stating explicitly
  in any write-up rather than presenting "3D" as if it were a single well-defined
  condition.
- Like the sibling project, sampling uses a fixed seed (`RNG` in `config.py`), so
  reruns with the same arguments pick the same windows.
- Only tested against Claude so far, per the "first with claude ai" scoping --
  a GPT-4o version could be added the same way the sibling project's
  `openai_client.py` was, once the Claude pilot results justify the extra cost.
