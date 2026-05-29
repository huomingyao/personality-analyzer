"""FAISS vector store implementation."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

import faiss
import numpy as np

from person_fenxi_core.config import FAISS_INDEX_PATH, VECTOR_DIM


class VectorStore:
    """FAISS-based vector store for semantic search."""

    def __init__(self, dim: int = VECTOR_DIM) -> None:
        self.dim = dim
        self.index: faiss.Index | None = None
        self.documents: Dict[int, Dict[str, Any]] = {}
        self._next_id = 0

    def create_index(self) -> None:
        """Create a new FAISS index."""
        self.index = faiss.IndexFlatL2(self.dim)
        self.documents = {}
        self._next_id = 0

    def add_vectors(
        self,
        vectors: np.ndarray,
        payloads: List[Dict[str, Any]],
    ) -> List[int]:
        """Add vectors with payloads to the index."""
        if self.index is None:
            self.create_index()

        if len(vectors) != len(payloads):
            msg = "Vectors and payloads must have same length"
            raise ValueError(msg)

        vectors = np.asarray(vectors, dtype=np.float32)
        if vectors.shape[1] != self.dim:
            msg = f"Vector dimension mismatch: expected {self.dim}, got {vectors.shape[1]}"
            raise ValueError(msg)

        doc_ids = []
        for vec, payload in zip(vectors, payloads):
            doc_id = self._next_id
            self._next_id += 1
            self.index.add(np.array([vec]))
            self.documents[doc_id] = payload
            doc_ids.append(doc_id)

        return doc_ids

    def search(
        self,
        query_vector: np.ndarray,
        k: int = 5,
    ) -> list[tuple[int, float, dict[str, Any]]]:
        """Search for top-k similar vectors."""
        if self.index is None:
            msg = "Index not created. Call create_index() first."
            raise RuntimeError(msg)

        query_vector = np.asarray(query_vector, dtype=np.float32).reshape(1, -1)
        distances, indices = self.index.search(query_vector, k)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx >= 0:
                results.append((int(idx), float(dist), self.documents.get(int(idx), {})))

        return results

    def save(self, path: Path | None = None) -> None:
        """Save index to disk."""
        path = path or FAISS_INDEX_PATH
        if self.index is not None:
            faiss.write_index(self.index, str(path))

        meta_path = path.with_suffix(".meta.json")
        meta = {
            "_next_id": self._next_id,
            "documents": self.documents,
        }
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2))

    def load(self, path: Path | None = None) -> None:
        """Load index from disk."""
        path = path or FAISS_INDEX_PATH
        if not path.exists():
            msg = f"Index file not found: {path}"
            raise FileNotFoundError(msg)

        self.index = faiss.read_index(str(path))

        meta_path = path.with_suffix(".meta.json")
        meta = json.loads(meta_path.read_text())
        self._next_id = meta["_next_id"]
        self.documents = meta["documents"]

    def clear(self) -> None:
        """Clear the index."""
        self.create_index()