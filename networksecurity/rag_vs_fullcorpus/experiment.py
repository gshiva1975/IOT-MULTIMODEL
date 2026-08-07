"""
experiment.py
-------------
Runs the Full-Corpus vs. RAG comparison across a sweep of corpus sizes and
(for RAG) a sweep of k values, and writes results to CSV.

Metrics collected per (strategy, corpus_size[, k]):
  - mean prompt tokens per call        (cost driver)
  - mean $ cost per call               (see cost_model.py for pricing caveat)
  - mean per-call latency              (context construction + retrieval time;
                                         NOT end-to-end LLM response latency --
                                         see README for what this does/doesn't measure)
  - one-time index build time & tokens (RAG only; 0 for full-corpus)
  - recall@k                           ("right answer present in what's sent
                                         to the model" rate -- 100% by
                                         construction for full-corpus, the
                                         real experimental variable for RAG)

Usage:
    python3 experiment.py
Outputs:
    results_by_size.csv     -- main sweep, k fixed at DEFAULT_K
    results_by_k.csv        -- secondary sweep of k at the largest corpus size
"""

import csv
import statistics as stats

from corpus import build_corpus, get_queries
from strategies import FullCorpusStrategy, RAGStrategy

CORPUS_SIZES = [100, 500, 1000, 2000, 5000, 10000]
DEFAULT_K = 5
K_SWEEP = [1, 3, 5, 10, 20, 50]
N_REPEATS = 3  # repeat each query this many times to smooth latency noise


def run_condition(strategy_cls, corpus_size: int, k: int):
    corpus = build_corpus(corpus_size)
    queries = get_queries()
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
        "p95_latency_ms": round(sorted(latencies)[int(0.95 * len(latencies)) - 1] * 1000, 4),
        "recall_at_k": round(sum(hits) / len(hits), 4),
        "index_build_time_s": round(index_stats.build_time_s, 4),
        "index_build_tokens": index_stats.build_tokens,
        "n_queries_evaluated": len(queries) * N_REPEATS,
    }


def main():
    print(f"Corpus sizes: {CORPUS_SIZES}")
    print(f"Fixed query set size: {len(get_queries())}, repeated x{N_REPEATS}\n")

    # --- Sweep 1: cost/latency/recall vs. corpus size, k fixed -------------
    rows = []
    for size in CORPUS_SIZES:
        row_full = run_condition(FullCorpusStrategy, size, k=DEFAULT_K)
        row_rag = run_condition(RAGStrategy, size, k=DEFAULT_K)
        rows.append(row_full)
        rows.append(row_rag)
        print(f"size={size:6d}  full: tokens={row_full['mean_tokens']:>9.0f}  "
              f"cost/call=${row_full['mean_cost_usd']:.6f}  recall={row_full['recall_at_k']:.3f}   |   "
              f"rag(k={DEFAULT_K}): tokens={row_rag['mean_tokens']:>7.0f}  "
              f"cost/call=${row_rag['mean_cost_usd']:.6f}  recall={row_rag['recall_at_k']:.3f}  "
              f"index_build={row_rag['index_build_time_s']:.3f}s")

    with open("results_by_size.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print("\nWrote results_by_size.csv")

    # --- Sweep 2: recall vs. k, at the largest corpus size ------------------
    largest = max(CORPUS_SIZES)
    k_rows = []
    for k in K_SWEEP:
        k_rows.append(run_condition(RAGStrategy, largest, k=k))
    with open("results_by_k.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(k_rows[0].keys()))
        writer.writeheader()
        writer.writerows(k_rows)
    print(f"Wrote results_by_k.csv (corpus_size={largest}, k in {K_SWEEP})")


if __name__ == "__main__":
    main()
