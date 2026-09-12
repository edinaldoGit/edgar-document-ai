from typing import Protocol
from uuid import UUID

from edgar.retrieval.results import RetrievedEvidence


class EvidenceSearcher(Protocol):
    def search(
        self,
        query_embedding: list[float],
        *,
        limit: int = 5,
        doc_id: UUID | None = None,
    ) -> list[RetrievedEvidence]: ...


class EvidenceRetriever(Protocol):
    def retrieve(
        self,
        query: str,
        *,
        limit: int = 5,
        doc_id: UUID | None = None,
    ) -> list[RetrievedEvidence]: ...
