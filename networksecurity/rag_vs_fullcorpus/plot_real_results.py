import csv
import matplotlib.pyplot as plt


def load_csv(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def savefig(name):
    plt.tight_layout()
    plt.savefig(name, dpi=150)
    plt.close()
    print(f"wrote {name}")


def fig_recall_vs_size():
    rows = load_csv("real_results_by_size.csv")
    full = sorted([r for r in rows if r["strategy"] == "full_corpus"], key=lambda r: int(r["corpus_size"]))
    rag = sorted([r for r in rows if r["strategy"] == "rag"], key=lambda r: int(r["corpus_size"]))
    sizes = [int(r["corpus_size"]) for r in full]
    plt.figure(figsize=(6, 4))
    plt.plot(sizes, [float(r["recall_at_k"]) for r in full], marker="o", label="Full-corpus (always 1.0)")
    plt.plot(sizes, [float(r["recall_at_k"]) for r in rag], marker="s", color="tab:orange", label="RAG (TF-IDF, k=5, real anchors)")
    plt.ylim(0, 1.05)
    plt.xlabel("Corpus size (15 real entries + synthetic padding)")
    plt.ylabel("Recall@k")
    plt.title("Recall vs. corpus size -- REAL CAPEC/CVE anchors\n(verified live against capec.mitre.org / nvd.nist.gov)")
    plt.legend()
    plt.grid(alpha=0.3)
    savefig("fig6_real_recall_vs_corpus_size.png")


def fig_recall_vs_k():
    rows = load_csv("real_results_by_k.csv")
    rows.sort(key=lambda r: int(r["k"]))
    ks = [int(r["k"]) for r in rows]
    recalls = [float(r["recall_at_k"]) for r in rows]
    plt.figure(figsize=(6, 4))
    plt.plot(ks, recalls, marker="o", color="tab:green")
    plt.ylim(0, 1.05)
    plt.xlabel("k (entries retrieved)")
    plt.ylabel("Recall@k")
    plt.title(f"Recall vs. k -- REAL anchors, corpus size {rows[0]['corpus_size']}")
    plt.grid(alpha=0.3)
    savefig("fig7_real_recall_vs_k.png")


if __name__ == "__main__":
    fig_recall_vs_size()
    fig_recall_vs_k()
