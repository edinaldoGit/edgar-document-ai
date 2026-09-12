from uuid import uuid4

from edgar.domain import BoundingBox, ComponentType, DocumentComponent
from edgar.ingestion.caption_association import associate_table_captions


def test_associate_table_caption_sets_parent_component_id():
    doc_id = uuid4()

    caption = DocumentComponent(
        doc_id=doc_id,
        page_index=28,
        component_type=ComponentType.TABLE_CAPTION,
        bbox=BoundingBox(
            x1=350,
            y1=477,
            x2=1961,
            y2=533,
        ),
    )

    table = DocumentComponent(
        doc_id=doc_id,
        page_index=28,
        component_type=ComponentType.TABLE,
        bbox=BoundingBox(
            x1=351,
            y1=535,
            x2=2248,
            y2=982,
        ),
    )

    footnote = DocumentComponent(
        doc_id=doc_id,
        page_index=28,
        component_type=ComponentType.TABLE_FOOTNOTE,
        bbox=BoundingBox(
            x1=349,
            y1=984,
            x2=829,
            y2=1031,
        ),
    )

    components = [footnote, table, caption]

    result = associate_table_captions(components)

    assert result is components
    assert caption.parent_component_id == table.component_id
    assert table.parent_component_id is None
    assert footnote.parent_component_id is None


def test_unmatched_table_caption_keeps_parent_empty():
    doc_id = uuid4()

    caption = DocumentComponent(
        doc_id=doc_id,
        page_index=0,
        component_type=ComponentType.TABLE_CAPTION,
        bbox=BoundingBox(
            x1=100,
            y1=100,
            x2=300,
            y2=130,
        ),
    )

    associate_table_captions([caption])

    assert caption.parent_component_id is None
