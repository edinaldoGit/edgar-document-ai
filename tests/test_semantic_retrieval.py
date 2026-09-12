from uuid import uuid4

import pytest

from edgar.domain import BoundingBox, ComponentType
from edgar.retrieval.results import RetrievedEvidence
from edgar.retrieval.semantic import SemanticRetriever


class FakeEmbedder:
    def __init__(self, embeddings):
        self.embeddings = embeddings
        self.calls = []

    def embed(self, texts):
        self.calls.append(texts)
        return self.embeddings


class FakeSearcher:
    def __init__(self, results):
        self.results = results
        self.calls = []

    def search(
        self,
        query_embedding,
        *,
        limit=5,
        doc_id=None,
    ):
        self.calls.append(
            (
                query_embedding,
                limit,
                doc_id,
            )
        )

        return self.results


def make_evidence():
    return RetrievedEvidence(
        component_id=uuid4(),
        doc_id=uuid4(),
        page_index=2,
        component_type=ComponentType.PLAIN_TEXT,
        bbox=BoundingBox(
            x1=10,
            y1=20,
            x2=100,
            y2=200,
        ),
        text="Evidência recuperada.",
        score=0.91,
    )


def test_retrieves_evidence_from_query():
    evidence = make_evidence()

    embedder = FakeEmbedder(
        [
            [0.1, 0.2, 0.3],
        ]
    )

    searcher = FakeSearcher([evidence])

    retriever = SemanticRetriever(
        embedder=embedder,
        searcher=searcher,
    )

    doc_id = uuid4()

    result = retriever.retrieve(
        "  Como funciona o EDGAR?  ",
        limit=3,
        doc_id=doc_id,
    )

    assert result == [evidence]

    assert embedder.calls == [
        [
            "Como funciona o EDGAR?",
        ]
    ]

    assert searcher.calls == [
        (
            [0.1, 0.2, 0.3],
            3,
            doc_id,
        )
    ]


def test_rejects_blank_query():
    retriever = SemanticRetriever(
        embedder=FakeEmbedder([]),
        searcher=FakeSearcher([]),
    )

    with pytest.raises(ValueError):
        retriever.retrieve("   ")


def test_rejects_non_positive_limit():
    retriever = SemanticRetriever(
        embedder=FakeEmbedder([]),
        searcher=FakeSearcher([]),
    )

    with pytest.raises(ValueError):
        retriever.retrieve(
            "pergunta",
            limit=0,
        )


def test_rejects_unexpected_query_embedding_count():
    retriever = SemanticRetriever(
        embedder=FakeEmbedder(
            [
                [0.1, 0.2],
                [0.3, 0.4],
            ]
        ),
        searcher=FakeSearcher([]),
    )

    with pytest.raises(RuntimeError):
        retriever.retrieve("pergunta")


def test_rejects_empty_query_embedding():
    retriever = SemanticRetriever(
        embedder=FakeEmbedder(
            [
                [],
            ]
        ),
        searcher=FakeSearcher([]),
    )

    with pytest.raises(RuntimeError):
        retriever.retrieve("pergunta")
