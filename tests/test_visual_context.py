from uuid import uuid4

import pytest

from edgar.domain import BoundingBox, ComponentType, DocumentComponent
from edgar.ingestion.visual_context import build_visual_text_context


def make_component(
    doc_id,
    component_type,
    *,
    parent_component_id=None,
    text_extracted=None,
):
    return DocumentComponent(
        doc_id=doc_id,
        page_index=0,
        component_type=component_type,
        bbox=BoundingBox(
            x1=10,
            y1=10,
            x2=100,
            y2=50,
        ),
        parent_component_id=parent_component_id,
        text_extracted=text_extracted,
    )


def test_builds_figure_context_from_caption():
    doc_id = uuid4()

    figure = make_component(
        doc_id,
        ComponentType.FIGURE,
    )

    caption = make_component(
        doc_id,
        ComponentType.FIGURE_CAPTION,
        parent_component_id=figure.component_id,
        text_extracted="Arquitetura proposta do sistema.",
    )

    context = build_visual_text_context(
        figure,
        [figure, caption],
    )

    assert context == ("Figure caption: Arquitetura proposta do sistema.")


def test_builds_table_context_from_caption_and_footnote():
    doc_id = uuid4()

    table = make_component(
        doc_id,
        ComponentType.TABLE,
    )

    caption = make_component(
        doc_id,
        ComponentType.TABLE_CAPTION,
        parent_component_id=table.component_id,
        text_extracted="Tabela 1 – Trabalhos relacionados.",
    )

    footnote = make_component(
        doc_id,
        ComponentType.TABLE_FOOTNOTE,
        parent_component_id=table.component_id,
        text_extracted="Fonte: Elaborado pelo autor.",
    )

    context = build_visual_text_context(
        table,
        [footnote, table, caption],
    )

    assert context == (
        "Table caption: Tabela 1 – Trabalhos relacionados.\n"
        "Table footnote: Fonte: Elaborado pelo autor."
    )


def test_ignores_unrelated_components():
    doc_id = uuid4()

    figure = make_component(
        doc_id,
        ComponentType.FIGURE,
    )

    unrelated_caption = make_component(
        doc_id,
        ComponentType.FIGURE_CAPTION,
        text_extracted="Outra figura.",
    )

    assert (
        build_visual_text_context(
            figure,
            [figure, unrelated_caption],
        )
        is None
    )


def test_ignores_related_component_without_text():
    doc_id = uuid4()

    table = make_component(
        doc_id,
        ComponentType.TABLE,
    )

    caption = make_component(
        doc_id,
        ComponentType.TABLE_CAPTION,
        parent_component_id=table.component_id,
        text_extracted=None,
    )

    assert build_visual_text_context(table, [table, caption]) is None


def test_rejects_non_visual_component():
    doc_id = uuid4()

    text = make_component(
        doc_id,
        ComponentType.PLAIN_TEXT,
    )

    with pytest.raises(ValueError):
        build_visual_text_context(text, [text])
