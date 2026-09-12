from uuid import uuid4

from edgar.domain import (
    BoundingBox,
    ComponentType,
    DocumentComponent,
)
from edgar.indexing.pipeline import IndexingPipeline


class FakeEmbedder:
    def __init__(self):
        self.calls = []

    def embed(self, texts):
        self.calls.append(texts)

        return [[0.1, 0.2, 0.3] for _ in texts]


class FakeStore:
    def __init__(self):
        self.calls = []

    def upsert(self, records):
        self.calls.append(records)


def test_indexes_components_end_to_end():
    component = DocumentComponent(
        doc_id=uuid4(),
        page_index=0,
        component_type=ComponentType.PLAIN_TEXT,
        bbox=BoundingBox(
            x1=10,
            y1=20,
            x2=200,
            y2=100,
        ),
        text_extracted=("O OCR é utilizado como fallback quando não existe texto nativo."),
    )

    embedder = FakeEmbedder()
    store = FakeStore()

    pipeline = IndexingPipeline(
        embedder=embedder,
        store=store,
    )

    result = pipeline.index([component])

    assert len(result) == 1

    assert embedder.calls == [["O OCR é utilizado como fallback quando não existe texto nativo."]]

    assert result[0].record.component_id == component.component_id
    assert result[0].embedding == (
        0.1,
        0.2,
        0.3,
    )

    assert store.calls == [result]


def test_skips_components_without_indexable_content():
    component = DocumentComponent(
        doc_id=uuid4(),
        page_index=0,
        component_type=ComponentType.ABANDON,
        bbox=BoundingBox(
            x1=10,
            y1=20,
            x2=200,
            y2=100,
        ),
    )

    embedder = FakeEmbedder()
    store = FakeStore()

    pipeline = IndexingPipeline(
        embedder=embedder,
        store=store,
    )

    result = pipeline.index([component])

    assert result == []
    assert embedder.calls == []
    assert store.calls == [[]]
