from uuid import UUID

from edgar.indexing.contracts import TextEmbedder
from edgar.retrieval.contracts import EvidenceSearcher
from edgar.retrieval.results import RetrievedEvidence


class SemanticRetriever:
    def __init__(
        self,
        *,
        embedder: TextEmbedder,
        searcher: EvidenceSearcher,
    ):
        self._embedder = embedder
        self._searcher = searcher

    def retrieve(
        self,
        query: str,
        *,
        limit: int = 5,
        doc_id: UUID | None = None,
    ) -> list[RetrievedEvidence]:
        query = query.strip()

        if not query:
            raise ValueError("Query must not be blank.")

        if limit <= 0:
            raise ValueError("Retrieval limit must be positive.")

        embeddings = self._embedder.embed([query])

        if len(embeddings) != 1:
            raise RuntimeError("Embedder returned an unexpected number of query embeddings.")

        query_embedding = embeddings[0]

        if not query_embedding:
            raise RuntimeError("Embedder returned an empty query embedding.")

        return self._searcher.search(
            query_embedding,
            limit=limit,
            doc_id=doc_id,
        )
