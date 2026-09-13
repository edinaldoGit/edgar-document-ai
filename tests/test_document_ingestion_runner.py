from uuid import uuid4

from edgar.domain import (
    BoundingBox,
    ComponentType,
    Document,
    DocumentComponent,
    DocumentPage,
)
from edgar.ingestion.document_runner import (
    DocumentIngestionRunner,
)


class FakeRasterizer:
    def __init__(self, pages):
        self.pages = pages
        self.calls = []

    def rasterize(self, document):
        self.calls.append(document)
        return self.pages


class FakePipeline:
    def __init__(self, results):
        self.results = results
        self.calls = []

    def process_page(
        self,
        document,
        page,
    ):
        self.calls.append(
            (
                document,
                page,
            )
        )

        return self.results[page.page_index]


def test_processes_all_document_pages():
    document = Document(
        doc_id=uuid4(),
        filename="documento.pdf",
        source_ref="/tmp/documento.pdf",
        page_count=2,
    )

    pages = [
        DocumentPage(
            doc_id=document.doc_id,
            page_index=0,
            width=1000,
            height=1400,
            render_dpi=300,
            image_ref=("documents/doc/pages/page_0001.png"),
        ),
        DocumentPage(
            doc_id=document.doc_id,
            page_index=1,
            width=1000,
            height=1400,
            render_dpi=300,
            image_ref=("documents/doc/pages/page_0002.png"),
        ),
    ]

    first_component = DocumentComponent(
        doc_id=document.doc_id,
        page_index=0,
        component_type=(ComponentType.PLAIN_TEXT),
        bbox=BoundingBox(
            x1=10,
            y1=20,
            x2=300,
            y2=100,
        ),
        text_extracted="Primeira página.",
    )

    second_component = DocumentComponent(
        doc_id=document.doc_id,
        page_index=1,
        component_type=(ComponentType.PLAIN_TEXT),
        bbox=BoundingBox(
            x1=20,
            y1=30,
            x2=400,
            y2=120,
        ),
        text_extracted="Segunda página.",
    )

    rasterizer = FakeRasterizer(pages)

    pipeline = FakePipeline(
        {
            0: [first_component],
            1: [second_component],
        }
    )

    runner = DocumentIngestionRunner(
        rasterizer=rasterizer,
        pipeline=pipeline,
    )

    result = runner.run(document)

    assert result == [
        first_component,
        second_component,
    ]

    assert rasterizer.calls == [document]

    assert pipeline.calls == [
        (
            document,
            pages[0],
        ),
        (
            document,
            pages[1],
        ),
    ]


def test_returns_empty_list_when_pages_have_no_components():
    document = Document(
        filename="documento.pdf",
        source_ref="/tmp/documento.pdf",
        page_count=1,
    )

    page = DocumentPage(
        doc_id=document.doc_id,
        page_index=0,
        width=1000,
        height=1400,
        render_dpi=300,
        image_ref=("documents/doc/pages/page_0001.png"),
    )

    runner = DocumentIngestionRunner(
        rasterizer=FakeRasterizer([page]),
        pipeline=FakePipeline(
            {
                0: [],
            }
        ),
    )

    assert runner.run(document) == []
