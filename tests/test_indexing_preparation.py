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
    visual_description=None,
    parent_component_id=None,
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
        visual_description=visual_description,
        parent_component_id=parent_component_id,
    )


def test_prepares_index_record_from_component():
    doc_id = uuid4()

    component = make_component(
        doc_id=doc_id,
        component_type=ComponentType.PLAIN_TEXT,
        text_extracted=("Recuperação semântica em granularidade fina."),
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


def test_absorbs_linked_figure_caption_into_figure():
    doc_id = uuid4()

    figure = make_component(
        doc_id=doc_id,
        component_type=ComponentType.FIGURE,
        visual_description=("Diagrama sobre a definição do metro."),
    )

    caption = make_component(
        doc_id=doc_id,
        component_type=ComponentType.FIGURE_CAPTION,
        text_extracted=("FIGURE 1.9 The meter is defined using the speed of light."),
        parent_component_id=figure.component_id,
    )

    records = prepare_index_records(
        [
            figure,
            caption,
        ]
    )

    assert len(records) == 1

    record = records[0]

    assert record.component_id == figure.component_id
    assert record.component_type == ComponentType.FIGURE
    assert "FIGURE 1.9" in record.text
    assert "Diagrama sobre a definição do metro." in record.text


def test_keeps_orphan_figure_caption_indexable():
    doc_id = uuid4()

    caption = make_component(
        doc_id=doc_id,
        component_type=ComponentType.FIGURE_CAPTION,
        text_extracted="Figura sem pai associado.",
    )

    records = prepare_index_records([caption])

    assert len(records) == 1
    assert records[0].component_id == caption.component_id
    assert records[0].text == "Figura sem pai associado."


def test_keeps_formula_caption_indexable():
    doc_id = uuid4()

    formula = make_component(
        doc_id=doc_id,
        component_type=ComponentType.ISOLATE_FORMULA,
    )

    caption = make_component(
        doc_id=doc_id,
        component_type=ComponentType.FORMULA_CAPTION,
        text_extracted="Equação 1 – Relação energia-massa.",
        parent_component_id=formula.component_id,
    )

    records = prepare_index_records(
        [
            formula,
            caption,
        ]
    )

    assert len(records) == 1
    assert records[0].component_id == caption.component_id
    assert records[0].component_type == ComponentType.FORMULA_CAPTION


def test_absorbs_table_caption_and_footnote_into_table():
    doc_id = uuid4()

    table = make_component(
        doc_id=doc_id,
        component_type=ComponentType.TABLE,
        visual_description="Tabela comparativa.",
    )

    caption = make_component(
        doc_id=doc_id,
        component_type=ComponentType.TABLE_CAPTION,
        text_extracted="Tabela 1 – Resultados.",
        parent_component_id=table.component_id,
    )

    footnote = make_component(
        doc_id=doc_id,
        component_type=ComponentType.TABLE_FOOTNOTE,
        text_extracted="Fonte: elaborado pelo autor.",
        parent_component_id=table.component_id,
    )

    records = prepare_index_records(
        [
            table,
            caption,
            footnote,
        ]
    )

    assert len(records) == 1

    record = records[0]

    assert record.component_id == table.component_id
    assert "Tabela 1 – Resultados." in record.text
    assert "Fonte: elaborado pelo autor." in record.text
