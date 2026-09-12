from uuid import uuid4

import pytest
from qdrant_client import QdrantClient

from edgar.domain import BoundingBox, ComponentType
from edgar.indexing.embedded_records import EmbeddedIndexRecord
from edgar.indexing.records import IndexRecord
from edgar.infrastructure.qdrant_vector_store import (
    QdrantVectorStore,
)


def make_embedded_record(
    *,
    embedding,
    text="Texto indexável.",
):
    return EmbeddedIndexRecord(
        record=IndexRecord(
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
            text=text,
            text_extracted=text,
            crop_ref="crop.png",
        ),
        embedding=tuple(embedding),
    )


def test_creates_collection_and_upserts_record():
    client = QdrantClient(":memory:")

    record = make_embedded_record(
        embedding=[
            1.0,
            0.0,
            0.0,
        ],
    )

    store = QdrantVectorStore(
        client=client,
        collection_name="test-components",
        vector_size=3,
    )

    store.upsert([record])

    assert client.collection_exists(
        collection_name="test-components",
    )

    points = client.retrieve(
        collection_name="test-components",
        ids=[
            str(record.record.component_id),
        ],
        with_payload=True,
        with_vectors=True,
    )

    assert len(points) == 1

    point = points[0]

    assert point.payload["component_id"] == str(record.record.component_id)
    assert point.payload["doc_id"] == str(record.record.doc_id)
    assert point.payload["page_index"] == 2
    assert point.payload["page_number"] == 3
    assert point.payload["component_type"] == "plain_text"
    assert point.payload["text"] == "Texto indexável."
    assert point.payload["text_extracted"] == "Texto indexável."
    assert point.payload["crop_ref"] == "crop.png"

    assert point.payload["bbox"] == {
        "x1": 10,
        "y1": 20,
        "x2": 100,
        "y2": 200,
    }


def test_rejects_embedding_with_wrong_dimension():
    client = QdrantClient(":memory:")

    record = make_embedded_record(
        embedding=[
            1.0,
            0.0,
        ],
    )

    store = QdrantVectorStore(
        client=client,
        vector_size=3,
    )

    with pytest.raises(ValueError):
        store.upsert([record])


def test_empty_upsert_does_not_create_collection():
    client = QdrantClient(":memory:")

    store = QdrantVectorStore(
        client=client,
        collection_name="empty-test",
        vector_size=3,
    )

    store.upsert([])

    assert not client.collection_exists(
        collection_name="empty-test",
    )


def test_search_returns_most_similar_evidence():
    client = QdrantClient(":memory:")

    first = make_embedded_record(
        embedding=[
            1.0,
            0.0,
            0.0,
        ],
        text="Primeira evidência.",
    )

    second = make_embedded_record(
        embedding=[
            0.0,
            1.0,
            0.0,
        ],
        text="Segunda evidência.",
    )

    store = QdrantVectorStore(
        client=client,
        collection_name="search-test",
        vector_size=3,
    )

    store.upsert(
        [
            first,
            second,
        ]
    )

    results = store.search(
        [
            1.0,
            0.0,
            0.0,
        ],
        limit=2,
    )

    assert len(results) == 2
    assert results[0].component_id == first.record.component_id
    assert results[0].text == "Primeira evidência."
    assert results[0].score == pytest.approx(1.0)
    assert results[0].bbox == first.record.bbox


def test_search_can_filter_by_document():
    client = QdrantClient(":memory:")

    first = make_embedded_record(
        embedding=[
            1.0,
            0.0,
            0.0,
        ],
        text="Documento um.",
    )

    second = make_embedded_record(
        embedding=[
            1.0,
            0.0,
            0.0,
        ],
        text="Documento dois.",
    )

    store = QdrantVectorStore(
        client=client,
        collection_name="filter-test",
        vector_size=3,
    )

    store.upsert(
        [
            first,
            second,
        ]
    )

    results = store.search(
        [
            1.0,
            0.0,
            0.0,
        ],
        doc_id=first.record.doc_id,
    )

    assert len(results) == 1
    assert results[0].doc_id == first.record.doc_id
    assert results[0].text == "Documento um."


def test_search_returns_empty_when_collection_does_not_exist():
    client = QdrantClient(":memory:")

    store = QdrantVectorStore(
        client=client,
        collection_name="missing",
        vector_size=3,
    )

    assert (
        store.search(
            [
                1.0,
                0.0,
                0.0,
            ]
        )
        == []
    )
