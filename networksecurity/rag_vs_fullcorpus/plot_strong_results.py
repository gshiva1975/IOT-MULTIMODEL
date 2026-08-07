import csv
import matplotlib.pyplot as plt

COLORS = {"tfidf": "tab:orange", "bm25": "tab:red", "lsa": "tab:purple"}
LABELS = {"tfidf": "TF-IDF", "bm25": "BM25", "lsa": "LSA (TF-IDF+SVD)"}


def load_csv(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def savefig(name):
    plt.tight_layout()
    plt.savefig(name, dpi=150)
    plt.close()
    print(f"wrote {name}")


def fig_recall_vs_size_with_ci():
    rows = load_csv("strong_results_by_size.csv")
    full = sorted([r for r in rows if r["strategy"] == "full_corpus"], key=lambda r: int(r["corpus_size"]))
    sizes = [int(r["corpus_size"]) for r in full]

    plt.figure(figsize=(7, 4.5))
    plt.plot(sizes, [float(r["recall_at_k"]) for r in full], marker="o", color="tab:blue",
              label="Full-corpus (always 1.0)", linewidth=2)

    for emb in ["tfidf", "bm25", "lsa"]:
        rag = sorted([r for r in rows if r["strategy"] == "rag" and r["embedder"] == emb],
                     key=lambda r: int(r["corpus_size"]))
        recalls = [float(r["recall_at_k"]) for r in rag]
        lo = [float(r["recall_ci_lo"]) for r in rag]
        hi = [float(r["recall_ci_hi"]) for r in rag]
        plt.plot(sizes, recalls, marker="s", color=COLORS[emb], label=f"RAG ({LABELS[emb]}, k=5)")
        plt.fill_between(sizes, lo, hi, color=COLORS[emb], alpha=0.15)

    plt.ylim(0, 1.05)
    plt.xlabel("Corpus size (real anchors + synthetic distractor padding)")
    plt.ylabel("Recall@5 (95% bootstrap CI shaded)")
    plt.title("Recall vs. corpus size -- three retrieval methods, real query set (n=45)")
    plt.legend(fontsize=9)
    plt.grid(alpha=0.3)
    savefig("fig10_strong_recall_vs_corpus_size.png")


def fig_recall_vs_k_with_ci():
    rows = load_csv("strong_results_by_k.csv")
    plt.figure(figsize=(7, 4.5))
    for emb in ["tfidf", "bm25", "lsa"]:
        sub = sorted([r for r in rows if r["embedder"] == emb], key=lambda r: int(r["k"]))
        ks = [int(r["k"]) for r in sub]
        recalls = [float(r["recall_at_k"]) for r in sub]
        lo = [float(r["recall_ci_lo"]) for r in sub]
        hi = [float(r["recall_ci_hi"]) for r in sub]
        plt.plot(ks, recalls, marker="o", color=COLORS[emb], label=LABELS[emb])
        plt.fill_between(ks, lo, hi, color=COLORS[emb], alpha=0.15)
    plt.ylim(0, 1.05)
    plt.xlabel("k (entries retrieved)")
    plt.ylabel("Recall@k (95% bootstrap CI shaded)")
    plt.title("Recall vs. k -- corpus size 2,000, real query set (n=45)")
    plt.legend(fontsize=9)
    plt.grid(alpha=0.3)
    savefig("fig11_strong_recall_vs_k.png")


if __name__ == "__main__":
    fig_recall_vs_size_with_ci()
    fig_recall_vs_k_with_ci()
