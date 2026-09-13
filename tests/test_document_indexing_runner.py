from uuid import uuid4

from edgar.domain import (
    BoundingBox,
    ComponentType,
    Document,
    DocumentComponent,
)
from edgar.indexing.document_runner import (
    DocumentIndexingRunner,
)


class FakeIngestionRunner:
    def __init__(self, components):
        self.components = components
        self.calls = []

    def run(self, document):
        self.calls.append(document)
        return self.components


class FakeIndexingPipeline:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def index(self, components):
        self.calls.append(components)
        return self.result


def test_ingests_and_indexes_document():
    document = Document(
        filename="documento.pdf",
        source_ref="/tmp/documento.pdf",
        page_count=1,
    )

    component = DocumentComponent(
        doc_id=document.doc_id,
        page_index=0,
        component_type=ComponentType.PLAIN_TEXT,
        bbox=BoundingBox(
            x1=10,
            y1=20,
            x2=300,
            y2=100,
        ),
        text_extracted="Conteúdo indexável.",
    )

    expected = [
        object(),
    ]

    ingestion_runner = FakeIngestionRunner([component])

    indexing_pipeline = FakeIndexingPipeline(expected)

    runner = DocumentIndexingRunner(
        ingestion_runner=ingestion_runner,
        indexing_pipeline=indexing_pipeline,
    )

    result = runner.run(document)

    assert result == expected

    assert ingestion_runner.calls == [document]

    assert indexing_pipeline.calls == [
        [
            component,
        ]
    ]


def test_indexes_empty_component_list():
    document = Document(
        doc_id=uuid4(),
        filename="documento.pdf",
        source_ref="/tmp/documento.pdf",
        page_count=1,
    )

    ingestion_runner = FakeIngestionRunner([])

    indexing_pipeline = FakeIndexingPipeline([])

    runner = DocumentIndexingRunner(
        ingestion_runner=ingestion_runner,
        indexing_pipeline=indexing_pipeline,
    )

    result = runner.run(document)

    assert result == []

    assert indexing_pipeline.calls == [[]]
