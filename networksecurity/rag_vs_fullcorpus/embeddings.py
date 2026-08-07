"""
embeddings.py
-------------
Pluggable embedder abstraction so RAGStrategy (strategies.py) isn't locked
to TF-IDF. In the sandbox this experiment was originally built in,
huggingface.co was network-blocked, so only TfidfEmbedder could run. On a
machine with normal internet access, SentenceTransformerEmbedder gives you
a real dense embedding model instead.

Usage in strategies.py:
    from embeddings import get_embedder
    embedder = get_embedder("auto")   # tries sentence-transformers, falls back to TF-IDF
"""

import time
from dataclasses import dataclass


@dataclass
class IndexBuildResult:
    build_time_s: float
    backend: str


class TfidfEmbedder:
    """Sparse lexical retrieval. Always available, no download required."""
    backend_name = "tfidf"

    def __init__(self):
        from sklearn.feature_extraction.text import TfidfVectorizer
        self._Vectorizer = TfidfVectorizer
        self._vectorizer = None
        self._matrix = None

    def fit(self, texts: list[str]) -> IndexBuildResult:
        t0 = time.perf_counter()
        self._vectorizer = self._Vectorizer(stop_words="english")
        self._matrix = self._vectorizer.fit_transform(texts)
        return IndexBuildResult(build_time_s=time.perf_counter() - t0, backend=self.backend_name)

    def similarities(self, query: str):
        from sklearn.metrics.pairwise import cosine_similarity
        q_vec = self._vectorizer.transform([query])
        return cosine_similarity(q_vec, self._matrix)[0]


class SentenceTransformerEmbedder:
    """
    Dense embedding retrieval using a local sentence-transformers model.
    Requires: pip install sentence-transformers
    First call downloads model weights from huggingface.co (~90MB for
    all-MiniLM-L6-v2) -- this is what was blocked in the sandbox.
    """
    backend_name = "sentence-transformers/all-MiniLM-L6-v2"

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer
        self._model = SentenceTransformer(model_name)
        self._embeddings = None

    def fit(self, texts: list[str]) -> IndexBuildResult:
        t0 = time.perf_counter()
        self._embeddings = self._model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
        return IndexBuildResult(build_time_s=time.perf_counter() - t0, backend=self.backend_name)

    def similarities(self, query: str):
        import numpy as np
        q_emb = self._model.encode([query], show_progress_bar=False, normalize_embeddings=True)[0]
        return self._embeddings @ q_emb  # cosine similarity, since both are normalized


class BM25Embedder:
    """
    Okapi BM25 (Robertson & Zaragoza, 2009) via the `rank_bm25` package.
    Still a sparse lexical method like TF-IDF, but with term-frequency
    saturation and document-length normalization that make it a stronger,
    more standard IR baseline -- BM25 is the default lexical baseline most
    RAG papers compare dense retrievers against. No model download required.
    """
    backend_name = "bm25"

    def __init__(self):
        from rank_bm25 import BM25Okapi
        self._BM25Okapi = BM25Okapi
        self._bm25 = None

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return text.lower().split()

    def fit(self, texts: list[str]) -> IndexBuildResult:
        t0 = time.perf_counter()
        tokenized = [self._tokenize(t) for t in texts]
        self._bm25 = self._BM25Okapi(tokenized)
        return IndexBuildResult(build_time_s=time.perf_counter() - t0, backend=self.backend_name)

    def similarities(self, query: str):
        return self._bm25.get_scores(self._tokenize(query))


class LSAEmbedder:
    """
    Latent Semantic Analysis (Deerwester et al., 1990): TF-IDF followed by
    truncated SVD, projecting into a low-dimensional space that captures
    co-occurrence structure beyond exact vocabulary overlap. This is the
    closest thing to a "semantic" retriever available without downloading
    external model weights -- a classical, fully local, offline technique,
    not a wrapper around TF-IDF with a different name.
    """
    backend_name = "lsa"

    def __init__(self, n_components: int = 100):
        self.n_components = n_components
        self._vectorizer = None
        self._svd = None
        self._doc_vecs = None

    def fit(self, texts: list[str]) -> IndexBuildResult:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.decomposition import TruncatedSVD
        import numpy as np

        t0 = time.perf_counter()
        self._vectorizer = TfidfVectorizer(stop_words="english")
        tfidf_matrix = self._vectorizer.fit_transform(texts)
        n_comp = max(1, min(self.n_components, tfidf_matrix.shape[0] - 1, tfidf_matrix.shape[1] - 1))
        self._svd = TruncatedSVD(n_components=n_comp, random_state=42)
        self._doc_vecs = self._svd.fit_transform(tfidf_matrix)
        norms = np.linalg.norm(self._doc_vecs, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        self._doc_vecs = self._doc_vecs / norms
        return IndexBuildResult(build_time_s=time.perf_counter() - t0, backend=self.backend_name)

    def similarities(self, query: str):
        import numpy as np
        q_tfidf = self._vectorizer.transform([query])
        q_vec = self._svd.transform(q_tfidf)[0]
        norm = np.linalg.norm(q_vec)
        if norm > 0:
            q_vec = q_vec / norm
        return self._doc_vecs @ q_vec


def get_embedder(kind: str = "auto"):
    """
    kind: "tfidf", "bm25", "lsa", "sentence-transformers", or "auto"
    (tries a real dense embedding model, falls back to TF-IDF if unavailable).
    """
    if kind == "tfidf":
        return TfidfEmbedder()
    if kind == "bm25":
        return BM25Embedder()
    if kind == "lsa":
        return LSAEmbedder()
    if kind == "sentence-transformers":
        return SentenceTransformerEmbedder()
    if kind == "auto":
        try:
            return SentenceTransformerEmbedder()
        except Exception as e:
            print(f"[embeddings] sentence-transformers unavailable ({e}); falling back to TF-IDF.")
            return TfidfEmbedder()
    raise ValueError(f"Unknown embedder kind: {kind}")
