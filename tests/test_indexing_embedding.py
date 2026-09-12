from uuid import uuid4

import pytest

from edgar.domain import BoundingBox, ComponentType
from edgar.indexing.embedding import embed_index_records
from edgar.indexing.records import IndexRecord


class FakeEmbedder:
    def __init__(self, embeddings):
        self.embeddings = embeddings
        self.calls = []

    def embed(self, texts):
        self.calls.append(texts)
        return self.embeddings


def make_record(text):
    return IndexRecord(
        component_id=uuid4(),
        doc_id=uuid4(),
        page_index=0,
        component_type=ComponentType.PLAIN_TEXT,
        bbox=BoundingBox(
            x1=10,
            y1=20,
            x2=100,
            y2=200,
        ),
        text=text,
    )


def test_embeds_index_records_in_order():
    first = make_record("Primeiro texto.")
    second = make_record("Segundo texto.")

    embedder = FakeEmbedder(
        [
            [0.1, 0.2, 0.3],
            [0.4, 0.5, 0.6],
        ]
    )

    result = embed_index_records(
        [
            first,
            second,
        ],
        embedder=embedder,
    )

    assert embedder.calls == [
        [
            "Primeiro texto.",
            "Segundo texto.",
        ]
    ]

    assert result[0].record == first
    assert result[0].embedding == (
        0.1,
        0.2,
        0.3,
    )
    assert result[0].dimension == 3

    assert result[1].record == second
    assert result[1].embedding == (
        0.4,
        0.5,
        0.6,
    )


def test_returns_empty_result_without_records():
    embedder = FakeEmbedder([])

    assert (
        embed_index_records(
            [],
            embedder=embedder,
        )
        == []
    )

    assert embedder.calls == []


def test_rejects_unexpected_embedding_count():
    records = [
        make_record("Primeiro texto."),
        make_record("Segundo texto."),
    ]

    embedder = FakeEmbedder(
        [
            [0.1, 0.2],
        ]
    )

    with pytest.raises(RuntimeError):
        embed_index_records(
            records,
            embedder=embedder,
        )
