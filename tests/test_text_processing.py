from uuid import uuid4

from edgar.domain import (
    BoundingBox,
    ComponentType,
    Document,
    DocumentComponent,
    DocumentPage,
)
from edgar.ingestion.text_processing import NativeTextProcessor


class RecordingTextExtractor:
    def __init__(self):
        self.extracted_component_ids = []

    def extract(self, document, page, component):
        self.extracted_component_ids.append(component.component_id)
        return f"text:{component.component_type.value}"


def make_component(doc_id, component_type):
    return DocumentComponent(
        doc_id=doc_id,
        page_index=0,
        component_type=component_type,
        bbox=BoundingBox(
            x1=10,
            y1=10,
            x2=20,
            y2=20,
        ),
    )


def test_process_extracts_text_only_from_textual_components():
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

    plain_text = make_component(
        doc_id,
        ComponentType.PLAIN_TEXT,
    )
    caption = make_component(
        doc_id,
        ComponentType.TABLE_CAPTION,
    )
    table = make_component(
        doc_id,
        ComponentType.TABLE,
    )
    figure = make_component(
        doc_id,
        ComponentType.FIGURE,
    )
    formula = make_component(
        doc_id,
        ComponentType.ISOLATE_FORMULA,
    )
    abandon = make_component(
        doc_id,
        ComponentType.ABANDON,
    )

    components = [
        plain_text,
        caption,
        table,
        figure,
        formula,
        abandon,
    ]

    extractor = RecordingTextExtractor()
    processor = NativeTextProcessor(extractor=extractor)

    result = processor.process(
        document,
        page,
        components,
    )

    assert result is components

    assert extractor.extracted_component_ids == [
        plain_text.component_id,
        caption.component_id,
    ]

    assert plain_text.text_extracted == "text:plain_text"
    assert caption.text_extracted == "text:table_caption"

    assert table.text_extracted is None
    assert figure.text_extracted is None
    assert formula.text_extracted is None
    assert abandon.text_extracted is None


def test_process_preserves_none_when_native_text_is_unavailable():
    class EmptyTextExtractor:
        def extract(self, document, page, component):
            return None

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

    component = make_component(
        doc_id,
        ComponentType.PLAIN_TEXT,
    )

    processor = NativeTextProcessor(
        extractor=EmptyTextExtractor(),
    )

    processor.process(
        document,
        page,
        [component],
    )

    assert component.text_extracted is None
