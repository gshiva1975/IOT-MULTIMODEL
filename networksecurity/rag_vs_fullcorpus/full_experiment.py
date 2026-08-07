"""
full_experiment.py
--------------------
The "run this on your own machine" experiment: uses full_real_corpus.json
(built by build_full_real_corpus.py from real, bulk-fetched CAPEC/NVD data
-- no synthetic padding) and lets you pick the retrieval backend, including
a real dense embedding model.

Usage:
    python3 full_experiment.py                                  # TF-IDF (always works)
    python3 full_experiment.py --embedder sentence-transformers  # real embeddings (needs the package + model download)
    python3 full_experiment.py --sizes 15,100,300,559            # custom corpus-size sweep

Requires full_real_corpus.json to exist (run fetch_capec_bulk.py,
fetch_nvd_bulk.py, build_full_real_corpus.py first -- or run_all.sh does
all of this for you).

Outputs:
    full_results_by_size.csv
    full_results_by_k.csv
"""

import argparse
import csv
import json
import statistics as stats

from real_corpus import REAL_ANCHOR_QUERIES
from strategies import FullCorpusStrategy, RAGStrategy

CORPUS_PATH = "full_real_corpus.json"
DEFAULT_K = 5
K_SWEEP = [1, 3, 5, 10, 20, 50]
N_REPEATS = 3


def load_full_corpus() -> list[dict]:
    with open(CORPUS_PATH) as f:
        return json.load(f)


def run_condition(strategy_cls, corpus: list[dict], k: int, embedder_kind: str):
    queries = REAL_ANCHOR_QUERIES
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

    return {
        "strategy": strategy_cls.name,
        "embedder": embedder_kind if strategy_cls.name == "rag" else "n/a",
        "corpus_size": len(corpus),
        "k": k if strategy_cls.name == "rag" else len(corpus),
        "mean_tokens": round(stats.mean(tokens), 1),
        "mean_cost_usd": round(stats.mean(costs), 6),
        "mean_latency_ms": round(stats.mean(latencies) * 1000, 4),
        "recall_at_k": round(sum(hits) / len(hits), 4),
        "index_build_time_s": round(index_stats.build_time_s, 4),
        "n_queries_evaluated": len(queries) * N_REPEATS,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--embedder", default="tfidf", choices=["tfidf", "sentence-transformers", "auto"])
    parser.add_argument("--sizes", default=None, help="comma-separated corpus sizes, e.g. 15,100,300,559")
    args = parser.parse_args()

    full_corpus = load_full_corpus()
    max_size = len(full_corpus)
    print(f"Loaded {max_size} real entries from {CORPUS_PATH}")
    print(f"Embedder: {args.embedder}")

    if args.sizes:
        sizes = [int(s) for s in args.sizes.split(",")]
    else:
        # sensible default sweep bounded by what's actually available
        candidates = [15, 50, 100, 250, 500, max_size]
        sizes = sorted(set(s for s in candidates if s <= max_size))

    print(f"Corpus-size sweep: {sizes}\n")

    rows = []
    for size in sizes:
        corpus_slice = full_corpus[:size]
        row_full = run_condition(FullCorpusStrategy, corpus_slice, DEFAULT_K, args.embedder)
        row_rag = run_condition(RAGStrategy, corpus_slice, DEFAULT_K, args.embedder)
        rows.append(row_full)
        rows.append(row_rag)
        print(f"size={size:5d}  full: recall={row_full['recall_at_k']:.3f}   |   "
              f"rag(k={DEFAULT_K}, {args.embedder}): recall={row_rag['recall_at_k']:.3f}  "
              f"index_build={row_rag['index_build_time_s']:.3f}s")

    with open("full_results_by_size.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print("\nWrote full_results_by_size.csv")

    largest_slice = full_corpus[:max_size]
    k_rows = [run_condition(RAGStrategy, largest_slice, k, args.embedder) for k in K_SWEEP]
    with open("full_results_by_k.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(k_rows[0].keys()))
        writer.writeheader()
        writer.writerows(k_rows)
    print(f"Wrote full_results_by_k.csv (corpus_size={max_size}, k in {K_SWEEP})")


if __name__ == "__main__":
    main()
