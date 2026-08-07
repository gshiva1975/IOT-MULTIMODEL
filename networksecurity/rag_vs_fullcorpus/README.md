# Full-Corpus vs. RAG Retrieval — Experiment Harness

Code for the "Paper 2" experiment: does full-corpus context-stuffing or RAG
retrieval win, and at what corpus size does the trade-off flip?

## What this measures (and what it doesn't)

This harness measures the **systems/retrieval-quality trade-off**: prompt
token cost, per-call latency, and recall@k (whether the correct CAPEC/CVE
entry actually ends up in front of the model) as the reference corpus grows
from 100 to 10,000 entries.

It does **not** call the real Claude classification pipeline, and it does
**not** reproduce ClearSight's reported classification accuracy or
wrong-citation numbers — those require live multimodal API calls against
real traffic images, which this sandbox has no credentials for. Wiring in
the real model is a small, contained change (see "Plugging in the real
model" below); everything here was built so that swap doesn't touch the
retrieval or corpus logic.

Retrieval uses **TF-IDF + cosine similarity**, not a neural embedding model.
This is disclosed on purpose: TF-IDF is local, deterministic, and needs no
model download, so the results are fully reproducible from this repo alone.
It is almost certainly a *worse* retriever than a production dense-embedding
model (Voyage, OpenAI, or a local sentence-transformer) — so the recall
numbers here should be read as a **lower bound** on what real RAG could
achieve, not as RAG's ceiling. If you want the paper's retrieval numbers to
reflect a production-grade retriever, swap the vectorizer in
`strategies.py::RAGStrategy` before running the final sweep for submission.

## Files

| File | Purpose |
|---|---|
| `corpus.py` | Generates the synthetic corpus (20 fixed "anchor" entries modeled on real CAPEC/CVE entries from the ClearSight report, padded with reproducible synthetic distractors to reach the target size) and the fixed 20-query test set. |
| `cost_model.py` | Token estimation heuristic + $ cost conversion. Pricing constant is a placeholder — **confirm current pricing before citing $ figures in the paper.** |
| `strategies.py` | `FullCorpusStrategy` and `RAGStrategy`, sharing one interface (`build_index()`, `query()`). |
| `experiment.py` | Runs the corpus-size sweep (`results_by_size.csv`) and the k sweep (`results_by_k.csv`). |
| `plot_results.py` | Renders the 5 figures below from the CSVs. |

## Reproducing

```bash
pip install scikit-learn pandas matplotlib
python3 experiment.py       # writes results_by_size.csv, results_by_k.csv
python3 plot_results.py     # writes fig1..fig5 .png
```

Everything is seeded (`corpus.RANDOM_SEED = 42`), so re-running produces
identical corpora and identical results.

## What the first run found

- **Cost scales linearly with corpus size for full-corpus, and stays flat
  for RAG.** At 100 entries, full-corpus costs ~3,500 tokens/call; at 10,000
  entries it's ~363,000 tokens/call (~100x). RAG (k=5) stays at ~180-190
  tokens/call regardless of corpus size, because it only ever sends 5 entries.
- **Full-corpus recall is 100% by construction** — the whole point of that
  design (per the ClearSight report) is that the right entry is always
  present. This harness confirms that's mechanically true; it can't fail to
  include the answer.
- **RAG (TF-IDF) recall@k plateaued around 60-70%** across corpus sizes,
  and **increasing k past 5 barely helped** (`fig4_recall_vs_k.png` — flat
  from k=5 to k=50 at the 10,000-entry corpus). That's a real finding worth
  writing up: for roughly 30% of the fixed query set, the correct entry
  never appeared even in the top 50 of 10,000 candidates. That's a lexical
  mismatch problem (the queries were deliberately paraphrased away from the
  entry text, simulating how an analyst's or model's natural-language
  description of traffic often won't share vocabulary with a formal CAPEC/
  CVE description) — exactly the kind of retrieval failure a dense embedding
  model is designed to close. This is the strongest argument in the harness
  for testing a real embedding model before drawing conclusions about
  production RAG viability.
- **Index build time stays small** (single-digit to low-hundred milliseconds
  even at 10,000 entries with TF-IDF) — a real embedding model would have
  materially higher one-time indexing cost/latency, which isn't captured here
  and should be measured before submission if a hosted embedding API is used.

## Plugging in the real model

To turn this into a true accuracy/hallucination-rate benchmark (matching the
core ClearSight paper's metrics), replace the `hit` boolean in
`CallResult` with an actual model call:

```python
# in strategies.py, inside query():
response = call_claude_multimodal(image, context_text, prompt_template)
correct = grade_citation(response, ground_truth_id)  # exact-match + "right explanation" check
```

That requires: (1) Anthropic API credentials, (2) real traffic images from
CIC-IoT-2023 (not just text queries), and (3) the grading logic from the
ClearSight report's Example 3 (a real CVE ID cited against the wrong
explanation should count as a miss, not a hit — this harness's `hit` field
only checks ID presence, not explanation correctness, since there's no LLM
output to grade yet).

## Update: real-data rerun (`real_corpus.py`, `real_experiment.py`)

Per request, the recall@k experiment was rerun on **real** CAPEC/CVE data instead of
the fully synthetic corpus above. What changed and what didn't:

- **15 real entries** (12 CAPEC + 3 CVE) were individually fetched live from
  `capec.mitre.org` and `nvd.nist.gov` during this session and are transcribed
  in `real_corpus.py` with their actual Name/Description text and source
  citation. These are not recalled from memory or templated -- each one was
  fetched and checked.
- Verification caught real errors in the original synthetic corpus's ID
  mappings: CAPEC-98 was assumed to be about port scanning and is actually
  "Phishing" (the real port-scanning ID is CAPEC-300); CAPEC-153 was assumed
  to be "Command Injection" and is actually "Input Data Manipulation." Both
  were corrected before this rerun. That mismatch-caught-by-checking is a
  small, unplanned demonstration of exactly the failure mode the ClearSight
  paper is about.
- **15 new natural-language queries** were hand-written against these real
  entries (same paraphrase discipline as before: written independently of
  the entry text, not copied from it).
- **What's still synthetic:** corpus sizes beyond 15 are padded with the same
  synthetic distractor generator from `corpus.py`, because individually
  fetching and verifying thousands of real CAPEC/CVE entries wasn't feasible
  with one-page-per-fetch retrieval in this session (MITRE's bulk XML/CSV
  downloads either exceed single-fetch size limits or come back as
  unreadable binary in this tool -- see "What was tried and didn't work"
  below). So: the *anchors and queries* -- the thing recall@k is actually
  measuring accuracy against -- are 100% real; the *background noise* is not.
- **Retrieval is still TF-IDF, not a dense embedding model.** `huggingface.co`
  returned `403 blocked-by-allowlist` from this sandbox's outbound proxy, so
  `sentence-transformers` and `fastembed` could install as Python packages
  but could not download any model weights. This is a sandbox network
  restriction, not a decision -- rerun with real network access and swap the
  vectorizer in `strategies.py::RAGStrategy` for a real embedding model
  before treating these recall numbers as final.

### What was tried and didn't work (for whoever picks this up next)

- `pip install sentence-transformers` -- installs, but loading any model
  requires downloading weights from huggingface.co, which the sandbox
  proxy blocks (403).
- `pip install fastembed` (ONNX-based, no torch) -- same blocker, same 403
  on huggingface.co once `httpx[socks]`/`socksio` were installed to get past
  an earlier proxy error.
- Bulk CAPEC download (`capec_latest.xml`, ~559 entries) via `mcp__workspace__web_fetch`
  -- fetches, but truncates around entry #14 because the full file exceeds
  the tool's per-call token limit; the `.csv.zip` / `.xml.zip` alternatives
  fetch but return unparseable binary through this tool.
- Direct `curl`/bash access to `capec.mitre.org` and `nvd.nist.gov` -- blocked
  by the sandbox's own outbound allowlist (403 blocked-by-allowlist),
  separate from the web_fetch tool, which does work for these two domains
  one page at a time.
- **What did work:** `mcp__workspace__web_fetch` one CAPEC/NVD detail page at a
  time. That's how all 15 real entries here were obtained -- it's just not
  a bulk-download path, so it doesn't scale to thousands of entries in one
  session.

### Real-data results

| Corpus size | Full-corpus recall | RAG (TF-IDF, k=5) recall |
|---|---|---|
| 15 (real anchors only, no padding) | 1.000 | 0.933 |
| 50 | 1.000 | 0.867 |
| 100 | 1.000 | 0.867 |
| 500 | 1.000 | 0.667 |
| 1000 | 1.000 | 0.667 |
| 2000 | 1.000 | 0.667 |

Two things worth noting in the writeup. First, TF-IDF recall on the real,
unpadded 15-entry corpus is 93.3% (14/15) -- close to perfect when there's
no noise, which is a sanity check that the retrieval mechanics work
correctly on real text, not just synthetic text. Second, recall degrades to
66.7% as synthetic distractor volume grows, which is the same qualitative
finding as the fully synthetic run, now anchored in real query/answer pairs
rather than entirely fabricated ones. `real_results_by_k.csv` shows recall
still hasn't recovered past 73.3% even at k=20 out of 2000, reinforcing that
raising k alone doesn't fully compensate for a weak (TF-IDF) retriever.

Figures: `fig6_real_recall_vs_corpus_size.png`, `fig7_real_recall_vs_k.png`.

## Running this yourself with full network access

Everything above ran inside a sandboxed environment whose outbound network
allowlist blocks `huggingface.co` (no dense embedding models) and
`capec.mitre.org` / `services.nvd.nist.gov` for direct/bulk requests (only
one-page-at-a-time fetches worked, via a special tool). None of that applies
on a normal machine. To get the real thing -- the full CAPEC catalog, a
broader set of real CVEs, and a real dense embedding model -- run:

```bash
pip install -r requirements.txt
./run_all.sh                                    # TF-IDF, no extra downloads
./run_all.sh --embedder sentence-transformers    # real embeddings (downloads ~90MB model on first run)
```

This runs, in order:

1. `fetch_capec_bulk.py` -- downloads the full CAPEC XML catalog (~559
   attack patterns) from `capec.mitre.org` and parses it into
   `capec_entries.json`. Confirmed to fail with `403 blocked-by-allowlist`
   in the sandbox; the download/parse logic itself was unit-tested against
   a sample XML snippet and works.
2. `fetch_nvd_bulk.py` -- queries the NVD REST API for CVEs matching a set
   of IoT/router/embedded-device keywords (Mirai, default password, UPnP
   buffer overflow, etc.) and writes `nvd_entries.json`. Set `NVD_API_KEY`
   in your environment (free key from
   [nvd.nist.gov/developers/request-an-api-key](https://nvd.nist.gov/developers/request-an-api-key))
   to avoid the slow unauthenticated rate limit (5 req/30s vs. 50 req/30s).
3. `build_full_real_corpus.py` -- merges both into `full_real_corpus.json`,
   keeping the 15 hand-verified anchor entries from `real_corpus.py` intact
   and deduplicating by ID. No synthetic entries anywhere in this file.
4. `full_experiment.py --embedder <tfidf|sentence-transformers>` -- runs the
   same recall@k / cost / latency sweep as before, but now the corpus-size
   sweep is bounded by (and drawn entirely from) real data -- up to however
   many entries `fetch_capec_bulk.py` + `fetch_nvd_bulk.py` actually pulled
   (expect roughly 559 + a few hundred, depending on `KEYWORD_SEARCHES` and
   NVD's current result counts).
5. `plot_full_results.py` -- produces `fig8_full_recall_vs_corpus_size.png`,
   `fig8b_full_tokens_vs_corpus_size.png`, `fig9_full_recall_vs_k.png`.

The `embeddings.py` module is what makes the embedder swappable:
`RAGStrategy(corpus, embedder_kind=...)` accepts `"tfidf"` (always works,
what every result in this repo so far used), `"sentence-transformers"` (real
dense embeddings via a local `all-MiniLM-L6-v2` model, needs
`pip install sentence-transformers` and one-time internet access to
huggingface.co to download weights), or `"auto"` (tries dense, falls back to
TF-IDF if unavailable). Swap in Voyage/OpenAI/Cohere embeddings instead by
adding a new class to `embeddings.py` with the same `fit()`/`similarities()`
interface -- `strategies.py` doesn't need to change.

Expect the real-embedding recall numbers to come in meaningfully higher than
the TF-IDF numbers reported above, especially at larger k -- TF-IDF's known
weakness is exactly the lexical-mismatch case this query set was designed to
stress (queries paraphrased away from the entry text), which is precisely
what dense embeddings are built to handle.

## Suggested next steps before submission

1. Swap TF-IDF for a real embedding model (sentence-transformers is a free,
   local option; Voyage/OpenAI embeddings if you want a hosted-cost data
   point too) and re-run — expect recall@k to improve materially.
2. Confirm the input token price in `cost_model.py` against current
   Anthropic pricing, and add an embedding-API price if you use a hosted
   embedding model, so `index_build_tokens` translates to a real $ figure.
3. Replace the synthetic corpus with your actual hand-verified CAPEC/CVE
   corpus (the ClearSight report references one, likely far smaller than
   10,000 today) — the size sweep is meant to *simulate* growth, but real
   corpus text will have different token density and vocabulary overlap
   than the synthetic distractors here.
4. If you want end-to-end accuracy (not just retrieval recall), wire in the
   real Claude calls as above and re-run against real traffic images.
