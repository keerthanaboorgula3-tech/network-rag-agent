"""Build a FAISS vector index over document chunks (TF-IDF vectors)."""
from __future__ import annotations

from dataclasses import dataclass

import faiss
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from .ingest import Chunk


@dataclass(frozen=True)
class Hit:
    source: str
    title: str
    text: str
    score: float


class ChunkIndex:
    """Cosine-similarity search: TF-IDF vectors are L2-normalised, so an
    inner-product FAISS index returns cosine similarity."""

    def __init__(self, chunks: list[Chunk]):
        self.chunks = chunks
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)
        matrix = self.vectorizer.fit_transform([c.text for c in chunks])
        vectors = np.ascontiguousarray(matrix.toarray(), dtype="float32")
        self.index = faiss.IndexFlatIP(vectors.shape[1])
        self.index.add(vectors)

    def search(self, query: str, k: int = 3) -> list[Hit]:
        q = self.vectorizer.transform([query]).toarray().astype("float32")
        k = max(1, min(k, len(self.chunks)))
        scores, ids = self.index.search(np.ascontiguousarray(q), k)
        hits = []
        for score, i in zip(scores[0], ids[0]):
            if i < 0 or score <= 0:  # score 0 means no shared terms
                continue
            c = self.chunks[i]
            hits.append(Hit(c.source, c.title, c.text, float(score)))
        return hits
