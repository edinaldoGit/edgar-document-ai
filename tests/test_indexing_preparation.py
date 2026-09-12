from uuid import uuid4

from edgar.domain import (
    BoundingBox,
    ComponentType,
    DocumentComponent,
)
from edgar.indexing.preparation import prepare_index_records


def make_component(
    *,
    doc_id,
    component_type,
    text_extracted=None,
):
    return DocumentComponent(
        doc_id=doc_id,
        page_index=2,
        component_type=component_type,
        bbox=BoundingBox(
            x1=10,
            y1=20,
            x2=200,
            y2=100,
        ),
        text_extracted=text_extracted,
    )


def test_prepares_index_record_from_component():
    doc_id = uuid4()

    component = make_component(
        doc_id=doc_id,
        component_type=ComponentType.PLAIN_TEXT,
        text_extracted="Recuperação semântica em granularidade fina.",
    )

    records = prepare_index_records([component])

    assert len(records) == 1

    record = records[0]

    assert record.component_id == component.component_id
    assert record.doc_id == doc_id
    assert record.page_index == 2
    assert record.page_number == 3
    assert record.component_type == ComponentType.PLAIN_TEXT
    assert record.bbox == component.bbox
    assert record.text == ("Recuperação semântica em granularidade fina.")
    assert record.text_extracted == component.text_extracted


def test_skips_component_without_indexable_representation():
    doc_id = uuid4()

    component = make_component(
        doc_id=doc_id,
        component_type=ComponentType.ABANDON,
        text_extracted="conteúdo descartado",
    )

    assert prepare_index_records([component]) == []
