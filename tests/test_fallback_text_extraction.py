from uuid import uuid4

from edgar.domain import (
    BoundingBox,
    ComponentType,
    Document,
    DocumentComponent,
    DocumentPage,
)
from edgar.ingestion.fallback_text_extraction import FallbackTextExtractor


class RecordingExtractor:
    def __init__(self, result):
        self.result = result
        self.calls = 0

    def extract(self, document, page, component):
        self.calls += 1
        return self.result


def make_context():
    doc_id = uuid4()

    document = Document(
        filename="document.pdf",
        source_ref="document.pdf",
        page_count=1,
        doc_id=doc_id,
    )

    page = DocumentPage(
        doc_id=doc_id,
        page_index=0,
        width=100,
        height=100,
        render_dpi=300,
        image_ref="page.png",
    )

    component = DocumentComponent(
        doc_id=doc_id,
        page_index=0,
        component_type=ComponentType.PLAIN_TEXT,
        bbox=BoundingBox(
            x1=10,
            y1=10,
            x2=90,
            y2=40,
        ),
    )

    return document, page, component


def test_returns_primary_text_without_calling_fallback():
    document, page, component = make_context()

    primary = RecordingExtractor("native text")
    fallback = RecordingExtractor("ocr text")

    extractor = FallbackTextExtractor(
        primary=primary,
        fallback=fallback,
    )

    result = extractor.extract(
        document,
        page,
        component,
    )

    assert result == "native text"
    assert primary.calls == 1
    assert fallback.calls == 0


def test_uses_fallback_when_primary_returns_none():
    document, page, component = make_context()

    primary = RecordingExtractor(None)
    fallback = RecordingExtractor("ocr text")

    extractor = FallbackTextExtractor(
        primary=primary,
        fallback=fallback,
    )

    result = extractor.extract(
        document,
        page,
        component,
    )

    assert result == "ocr text"
    assert primary.calls == 1
    assert fallback.calls == 1


def test_returns_none_when_both_extractors_fail():
    document, page, component = make_context()

    primary = RecordingExtractor(None)
    fallback = RecordingExtractor(None)

    extractor = FallbackTextExtractor(
        primary=primary,
        fallback=fallback,
    )

    result = extractor.extract(
        document,
        page,
        component,
    )

    assert result is None
    assert primary.calls == 1
    assert fallback.calls == 1
