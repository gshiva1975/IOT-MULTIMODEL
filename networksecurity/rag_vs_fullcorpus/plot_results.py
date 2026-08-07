"""
plot_results.py
----------------
Reads results_by_size.csv and results_by_k.csv (produced by experiment.py)
and renders the figures a paper submission would want:

  fig1_tokens_vs_corpus_size.png   -- cost driver: prompt tokens vs. corpus size
  fig2_cost_vs_corpus_size.png     -- $ cost per call vs. corpus size
  fig3_recall_vs_corpus_size.png   -- recall@k vs. corpus size (k fixed)
  fig4_recall_vs_k.png             -- recall vs. k at the largest corpus size
  fig5_latency_vs_corpus_size.png  -- context-construction latency vs. corpus size
"""

import csv
import matplotlib.pyplot as plt


def load_csv(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def by_size():
    rows = load_csv("results_by_size.csv")
    full = [r for r in rows if r["strategy"] == "full_corpus"]
    rag = [r for r in rows if r["strategy"] == "rag"]
    full.sort(key=lambda r: int(r["corpus_size"]))
    rag.sort(key=lambda r: int(r["corpus_size"]))
    return full, rag


def savefig(name):
    plt.tight_layout()
    plt.savefig(name, dpi=150)
    plt.close()
    print(f"wrote {name}")


def fig_tokens():
    full, rag = by_size()
    sizes = [int(r["corpus_size"]) for r in full]
    plt.figure(figsize=(6, 4))
    plt.plot(sizes, [float(r["mean_tokens"]) for r in full], marker="o", label="Full-corpus context-stuffing")
    plt.plot(sizes, [float(r["mean_tokens"]) for r in rag], marker="s", label="RAG (TF-IDF, k=5)")
    plt.xlabel("Corpus size (entries)")
    plt.ylabel("Mean prompt tokens per call")
    plt.title("Prompt token cost vs. corpus size")
    plt.legend()
    plt.grid(alpha=0.3)
    savefig("fig1_tokens_vs_corpus_size.png")


def fig_cost():
    full, rag = by_size()
    sizes = [int(r["corpus_size"]) for r in full]
    plt.figure(figsize=(6, 4))
    plt.plot(sizes, [float(r["mean_cost_usd"]) for r in full], marker="o", label="Full-corpus context-stuffing")
    plt.plot(sizes, [float(r["mean_cost_usd"]) for r in rag], marker="s", label="RAG (TF-IDF, k=5)")
    plt.xlabel("Corpus size (entries)")
    plt.ylabel("Estimated $ cost per call")
    plt.title("Per-call input cost vs. corpus size\n(pricing constant is a placeholder -- see cost_model.py)")
    plt.legend()
    plt.grid(alpha=0.3)
    savefig("fig2_cost_vs_corpus_size.png")


def fig_recall_vs_size():
    full, rag = by_size()
    sizes = [int(r["corpus_size"]) for r in full]
    plt.figure(figsize=(6, 4))
    plt.plot(sizes, [float(r["recall_at_k"]) for r in full], marker="o", label="Full-corpus (always 1.0 by construction)")
    plt.plot(sizes, [float(r["recall_at_k"]) for r in rag], marker="s", label="RAG (TF-IDF, k=5)")
    plt.ylim(0, 1.05)
    plt.xlabel("Corpus size (entries)")
    plt.ylabel("Recall@k (correct entry present in what's sent to the model)")
    plt.title("Retrieval recall vs. corpus size")
    plt.legend()
    plt.grid(alpha=0.3)
    savefig("fig3_recall_vs_corpus_size.png")


def fig_recall_vs_k():
    rows = load_csv("results_by_k.csv")
    rows.sort(key=lambda r: int(r["k"]))
    ks = [int(r["k"]) for r in rows]
    recalls = [float(r["recall_at_k"]) for r in rows]
    plt.figure(figsize=(6, 4))
    plt.plot(ks, recalls, marker="o", color="tab:orange")
    plt.ylim(0, 1.05)
    plt.xlabel("k (entries retrieved)")
    plt.ylabel("Recall@k")
    plt.title(f"Recall vs. k at largest corpus size ({rows[0]['corpus_size']} entries)")
    plt.grid(alpha=0.3)
    savefig("fig4_recall_vs_k.png")


def fig_latency():
    full, rag = by_size()
    sizes = [int(r["corpus_size"]) for r in full]
    plt.figure(figsize=(6, 4))
    plt.plot(sizes, [float(r["mean_latency_ms"]) for r in full], marker="o", label="Full-corpus (serialize all entries)")
    plt.plot(sizes, [float(r["mean_latency_ms"]) for r in rag], marker="s", label="RAG (TF-IDF search, k=5)")
    plt.xlabel("Corpus size (entries)")
    plt.ylabel("Mean per-call latency (ms)")
    plt.title("Context-construction latency vs. corpus size\n(local CPU time; excludes LLM inference time)")
    plt.legend()
    plt.grid(alpha=0.3)
    savefig("fig5_latency_vs_corpus_size.png")


if __name__ == "__main__":
    fig_tokens()
    fig_cost()
    fig_recall_vs_size()
    fig_recall_vs_k()
    fig_latency()
