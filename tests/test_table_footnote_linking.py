from uuid import uuid4

from edgar.domain import BoundingBox, ComponentType, DocumentComponent
from edgar.ingestion.table_association import associate_table_footnotes


def test_associate_table_footnote_sets_parent_component_id():
    doc_id = uuid4()

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

    components = [table, footnote]

    result = associate_table_footnotes(components)

    assert result is components
    assert footnote.parent_component_id == table.component_id
    assert table.parent_component_id is None


def test_unmatched_table_footnote_keeps_parent_empty():
    doc_id = uuid4()

    footnote = DocumentComponent(
        doc_id=doc_id,
        page_index=0,
        component_type=ComponentType.TABLE_FOOTNOTE,
        bbox=BoundingBox(
            x1=100,
            y1=100,
            x2=200,
            y2=130,
        ),
    )

    associate_table_footnotes([footnote])

    assert footnote.parent_component_id is None
