"""
real_experiment.py
-------------------
Re-runs the recall@k / cost / latency sweep using REAL_ANCHOR_ENTRIES and
REAL_ANCHOR_QUERIES from real_corpus.py (15 real, individually-verified
CAPEC/CVE entries and hand-written queries) instead of the fully synthetic
anchors in corpus.py.

Corpus sizes are still grown with the same synthetic distractor generator
(corpus._distractor_entry) as before, because building 10,000 individually
verified real entries isn't feasible with per-page fetches in this session
(see README). The anchors and the queries you should care about for the
recall number -- the actual dependent variable -- are 100% real; only the
background noise padding the corpus out to size is synthetic. This is
disclosed, not hidden.

Retrieval is still TF-IDF (see strategies.py) -- HuggingFace, and therefore
every local dense-embedding model, was blocked by this sandbox's network
allowlist (403 blocked-by-allowlist), so no dense embedding model could be
downloaded here. That's a sandbox limitation, not a design choice; swap in
sentence-transformers/Voyage/OpenAI embeddings in strategies.py wherever you
run this with normal network access, and recall@k should be reported as
"TF-IDF, sandbox-constrained" until that's redone.

Usage:
    python3 real_experiment.py
Outputs:
    real_results_by_size.csv
    real_results_by_k.csv
"""

import csv
import statistics as stats
import random

from corpus import _distractor_entry
from real_corpus import REAL_ANCHOR_ENTRIES, REAL_ANCHOR_QUERIES
from strategies import FullCorpusStrategy, RAGStrategy

CORPUS_SIZES = [15, 50, 100, 500, 1000, 2000]  # starts at 15 = the real corpus alone, no padding
DEFAULT_K = 5
K_SWEEP = [1, 3, 5, 10, 15, 20]
N_REPEATS = 3
SEED = 42


def build_real_corpus(target_size: int, seed: int = SEED) -> list[dict]:
    if target_size < len(REAL_ANCHOR_ENTRIES):
        raise ValueError(f"target_size must be >= {len(REAL_ANCHOR_ENTRIES)} (number of real anchors)")
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


def run_condition(strategy_cls, corpus_size: int, k: int):
    corpus = build_real_corpus(corpus_size)
    queries = REAL_ANCHOR_QUERIES
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

    return {
        "strategy": strategy_cls.name,
        "corpus_size": corpus_size,
        "k": k if strategy_cls.name == "rag" else corpus_size,
        "mean_tokens": round(stats.mean(tokens), 1),
        "mean_cost_usd": round(stats.mean(costs), 6),
        "mean_latency_ms": round(stats.mean(latencies) * 1000, 4),
        "recall_at_k": round(sum(hits) / len(hits), 4),
        "index_build_time_s": round(index_stats.build_time_s, 4),
        "n_queries_evaluated": len(queries) * N_REPEATS,
    }


def main():
    print(f"Real anchor entries: {len(REAL_ANCHOR_ENTRIES)}, real queries: {len(REAL_ANCHOR_QUERIES)}")
    print(f"Corpus sizes (real anchors + synthetic padding): {CORPUS_SIZES}\n")

    rows = []
    for size in CORPUS_SIZES:
        row_full = run_condition(FullCorpusStrategy, size, k=DEFAULT_K)
        row_rag = run_condition(RAGStrategy, size, k=DEFAULT_K)
        rows.append(row_full)
        rows.append(row_rag)
        print(f"size={size:5d}  full: recall={row_full['recall_at_k']:.3f} tokens={row_full['mean_tokens']:>8.0f}   |   "
              f"rag(k={DEFAULT_K}): recall={row_rag['recall_at_k']:.3f} tokens={row_rag['mean_tokens']:>6.0f}")

    with open("real_results_by_size.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print("\nWrote real_results_by_size.csv")

    largest = max(CORPUS_SIZES)
    k_rows = [run_condition(RAGStrategy, largest, k=k) for k in K_SWEEP]
    with open("real_results_by_k.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(k_rows[0].keys()))
        writer.writeheader()
        writer.writerows(k_rows)
    print(f"Wrote real_results_by_k.csv (corpus_size={largest}, k in {K_SWEEP})")


if __name__ == "__main__":
    main()
