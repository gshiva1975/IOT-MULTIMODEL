"""
strategies.py
-------------
Two context-construction strategies for the classification+citation call:

  FullCorpusStrategy  -- serializes the ENTIRE corpus into the prompt every
                          call (ClearSight's current, measured design).
  RAGStrategy          -- builds a TF-IDF vector index over the corpus once
                          (offline, local, "in the Agent Node"), then at
                          query time retrieves only the top-k most similar
                          entries and serializes just those.

TF-IDF + cosine similarity is used as the retrieval backbone here instead of
a neural embedding model. This is a deliberate, disclosed simplification:
TF-IDF is fast, fully local/offline, deterministic, and needs no model
download or GPU -- appropriate for a systems/cost benchmark whose question is
"how do cost, latency, and retrieval recall scale with corpus size," not
"what's the best possible embedding model." A production RAG system would
likely swap in a dense embedding model (e.g. Voyage, OpenAI, or a local
sentence-transformer); the harness is structured so that swap only touches
this file (`RAGStrategy.fit` / `RAGStrategy.retrieve`).

Both strategies expose the same interface so `experiment.py` can call them
interchangeably.
"""

import time
from dataclasses import dataclass, field

from corpus import entry_text
from cost_model import estimate_tokens, estimate_cost_usd
from embeddings import get_embedder


@dataclass
class CallResult:
    tokens: int
    cost_usd: float
    latency_s: float          # time to construct context for this single query (excludes one-time indexing)
    retrieved_ids: list       # entry ids actually placed in the prompt context
    hit: bool                 # True if ground-truth id is among retrieved_ids


@dataclass
class IndexStats:
    build_time_s: float = 0.0
    build_tokens: int = 0     # tokens "spent" once, at index-build time (0 for full-corpus; embedding cost for RAG)


class FullCorpusStrategy:
    """Every call gets the entire corpus. No index to build."""

    name = "full_corpus"

    def __init__(self, corpus: list[dict]):
        self.corpus = corpus
        # Precompute the serialized corpus text once per corpus object,
        # mirroring the real system (the corpus doesn't change between calls
        # within one experiment condition) -- but we still re-measure the
        # per-call construction cost below to keep latency comparable to RAG.
        self._texts = [entry_text(e) for e in corpus]
        self._ids = [e["id"] for e in corpus]

    def build_index(self) -> IndexStats:
        return IndexStats(build_time_s=0.0, build_tokens=0)

    def query(self, query_text: str, ground_truth_id: str, k: int = 5) -> CallResult:
        t0 = time.perf_counter()
        full_text = "\n".join(self._texts) + "\n" + query_text
        latency = time.perf_counter() - t0
        tokens = estimate_tokens(full_text)
        return CallResult(
            tokens=tokens,
            cost_usd=estimate_cost_usd(tokens),
            latency_s=latency,
            retrieved_ids=self._ids,
            hit=ground_truth_id in self._ids,
        )


class RAGStrategy:
    """
    Top-k retrieval over the corpus, per query. Retrieval backend is
    pluggable via `embedder_kind` ("tfidf", "sentence-transformers", or
    "auto") -- see embeddings.py. Defaults to "tfidf" so existing callers
    (real_experiment.py, experiment.py) keep working unchanged; pass
    embedder_kind="sentence-transformers" for a real dense embedding model
    (requires `pip install sentence-transformers` and network access to
    huggingface.co on first run to download weights).
    """

    name = "rag"

    def __init__(self, corpus: list[dict], embedder_kind: str = "tfidf"):
        self.corpus = corpus
        self._texts = [entry_text(e) for e in corpus]
        self._ids = [e["id"] for e in corpus]
        self._embedder = get_embedder(embedder_kind)

    def build_index(self) -> IndexStats:
        result = self._embedder.fit(self._texts)
        # One-time "embedding" cost: in a real system with a hosted embedding
        # API this would be billed once per corpus entry. Locally it's $0,
        # but we still report the token volume processed for parity with a
        # hosted-embedding cost model.
        build_tokens = sum(estimate_tokens(t) for t in self._texts)
        return IndexStats(build_time_s=result.build_time_s, build_tokens=build_tokens)

    def query(self, query_text: str, ground_truth_id: str, k: int = 5) -> CallResult:
        t0 = time.perf_counter()
        sims = self._embedder.similarities(query_text)
        top_k_idx = sims.argsort()[::-1][:k]
        retrieved_ids = [self._ids[i] for i in top_k_idx]
        retrieved_texts = [self._texts[i] for i in top_k_idx]
        context_text = "\n".join(retrieved_texts) + "\n" + query_text
        latency = time.perf_counter() - t0
        tokens = estimate_tokens(context_text)
        return CallResult(
            tokens=tokens,
            cost_usd=estimate_cost_usd(tokens),
            latency_s=latency,
            retrieved_ids=retrieved_ids,
            hit=ground_truth_id in retrieved_ids,
        )
