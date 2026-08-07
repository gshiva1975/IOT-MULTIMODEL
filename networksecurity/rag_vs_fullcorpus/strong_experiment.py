"""
strong_experiment.py
----------------------
Strengthened version of real_experiment.py, addressing the main weaknesses
of the first pass:

  1. Three retrieval backends instead of one: TF-IDF, BM25 (Okapi), and LSA
     (TF-IDF + truncated SVD). All three are real, established, fully local
     retrieval methods requiring no external model download -- this is the
     strongest retrieval comparison achievable without network access to
     huggingface.co (blocked in this sandbox; see README).
  2. 45 real queries instead of 15 (REAL_ANCHOR_QUERIES_ALL: the original
     15 hand-written queries plus 2 additional independently-written
     paraphrases per anchor), which cuts the "one query flips the result"
     granularity from 6.7 percentage points to 2.2.
  3. Bootstrap 95% confidence intervals on every recall estimate (10,000
     resamples), so results are reported with uncertainty instead of as
     bare point estimates.

Still real anchors + real queries; corpus growth beyond 15 entries still
uses the synthetic distractor generator (see real_experiment.py / README for
why, and full_experiment.py for the fully-real-data path once you have
unrestricted network access).

Usage:
    python3 strong_experiment.py
Outputs:
    strong_results_by_size.csv
    strong_results_by_k.csv
"""

import csv
import random
import statistics as stats

import numpy as np

from corpus import _distractor_entry
from real_corpus import REAL_ANCHOR_ENTRIES, REAL_ANCHOR_QUERIES_ALL
from strategies import FullCorpusStrategy, RAGStrategy

CORPUS_SIZES = [15, 50, 100, 500, 1000, 2000]
DEFAULT_K = 5
K_SWEEP = [1, 3, 5, 10, 15, 20]
N_REPEATS = 2  # queries are now 3x more numerous, so fewer repeats needed for stable latency estimates
SEED = 42
N_BOOTSTRAP = 10000
EMBEDDERS = ["tfidf", "bm25", "lsa"]


def build_real_corpus(target_size: int, seed: int = SEED) -> list[dict]:
    if target_size < len(REAL_ANCHOR_ENTRIES):
        raise ValueError(f"target_size must be >= {len(REAL_ANCHOR_ENTRIES)}")
    rng = random.Random(seed)
    corpus = []
    for eid, kind, name, families, desc in REAL_ANCHOR_ENTRIES:
        corpus.append({"id": eid, "kind": kind, "name": name, "attack_families": families,
                        "description": desc, "source_url": "(see real_corpus.py for fetched source)"})
    n_distractors = target_size - len(REAL_ANCHOR_ENTRIES)
    for i in range(n_distractors):
        corpus.append(_distractor_entry(i, rng))
    shuffle_rng = random.Random(seed + 1)
    shuffle_rng.shuffle(corpus)
    return corpus


def bootstrap_ci(hits: list[bool], n_boot: int = N_BOOTSTRAP, seed: int = SEED):
    """Bootstrap 95% CI for a recall estimate (mean of a 0/1 list)."""
    arr = np.array(hits, dtype=float)
    rng = np.random.default_rng(seed)
    n = len(arr)
    boot_means = rng.choice(arr, size=(n_boot, n), replace=True).mean(axis=1)
    lo, hi = np.percentile(boot_means, [2.5, 97.5])
    return float(lo), float(hi)


def run_condition(strategy_cls, corpus: list[dict], k: int, embedder_kind: str):
    queries = REAL_ANCHOR_QUERIES_ALL
    if strategy_cls.name == "rag":
        strat = strategy_cls(corpus, embedder_kind=embedder_kind)
    else:
        strat = strategy_cls(corpus)
    index_stats = strat.build_index()

    tokens, costs, latencies, hits = [], [], [], []
    for _ in range(N_REPEATS):
        for q_text, gt_id in queries:
            r = strat.query(q_text, gt_id, k=k)
            tokens.append(r.tokens)
            costs.append(r.cost_usd)
            latencies.append(r.latency_s)
            hits.append(r.hit)

    recall = sum(hits) / len(hits)
    ci_lo, ci_hi = bootstrap_ci(hits)

    return {
        "strategy": strategy_cls.name,
        "embedder": embedder_kind if strategy_cls.name == "rag" else "n/a",
        "corpus_size": len(corpus),
        "k": k if strategy_cls.name == "rag" else len(corpus),
        "mean_tokens": round(stats.mean(tokens), 1),
        "mean_cost_usd": round(stats.mean(costs), 6),
        "mean_latency_ms": round(stats.mean(latencies) * 1000, 4),
        "recall_at_k": round(recall, 4),
        "recall_ci_lo": round(ci_lo, 4),
        "recall_ci_hi": round(ci_hi, 4),
        "index_build_time_s": round(index_stats.build_time_s, 4),
        "n_queries_evaluated": len(queries) * N_REPEATS,
    }


def main():
    print(f"Real anchors: {len(REAL_ANCHOR_ENTRIES)}, real queries (expanded): {len(REAL_ANCHOR_QUERIES_ALL)}")
    print(f"Corpus sizes: {CORPUS_SIZES}")
    print(f"Embedders: {EMBEDDERS}\n")

    rows = []
    for size in CORPUS_SIZES:
        corpus = build_real_corpus(size)
        row_full = run_condition(FullCorpusStrategy, corpus, DEFAULT_K, "n/a")
        rows.append(row_full)
        line = f"size={size:5d}  full: recall={row_full['recall_at_k']:.3f}"
        for emb in EMBEDDERS:
            row = run_condition(RAGStrategy, corpus, DEFAULT_K, emb)
            rows.append(row)
            line += f"   |   {emb}: {row['recall_at_k']:.3f} [{row['recall_ci_lo']:.3f}, {row['recall_ci_hi']:.3f}]"
        print(line)

    with open("strong_results_by_size.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print("\nWrote strong_results_by_size.csv")

    largest = max(CORPUS_SIZES)
    corpus = build_real_corpus(largest)
    k_rows = []
    for emb in EMBEDDERS:
        for k in K_SWEEP:
            k_rows.append(run_condition(RAGStrategy, corpus, k, emb))
    with open("strong_results_by_k.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(k_rows[0].keys()))
        writer.writeheader()
        writer.writerows(k_rows)
    print(f"Wrote strong_results_by_k.csv (corpus_size={largest}, k in {K_SWEEP}, embedders={EMBEDDERS})")


if __name__ == "__main__":
    main()
