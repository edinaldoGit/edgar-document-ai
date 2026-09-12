from uuid import uuid4

from edgar.domain import (
    BoundingBox,
    ComponentType,
    DocumentComponent,
    TableStructure,
)
from edgar.indexing.representation import (
    build_indexable_text,
    table_structure_to_text,
)


def component(
    *,
    doc_id,
    component_type,
    text_extracted=None,
    visual_description=None,
    table_structure=None,
    parent_component_id=None,
):
    return DocumentComponent(
        doc_id=doc_id,
        page_index=0,
        component_type=component_type,
        bbox=BoundingBox(
            x1=10,
            y1=20,
            x2=200,
            y2=100,
        ),
        text_extracted=text_extracted,
        visual_description=visual_description,
        table_structure=table_structure,
        parent_component_id=parent_component_id,
    )


def test_uses_native_text_for_textual_component():
    doc_id = uuid4()

    text = component(
        doc_id=doc_id,
        component_type=ComponentType.PLAIN_TEXT,
        text_extracted="Arquiteturas RAG recuperam evidências.",
    )

    assert (
        build_indexable_text(
            text,
            [text],
        )
        == "Arquiteturas RAG recuperam evidências."
    )


def test_builds_figure_representation_from_caption_and_description():
    doc_id = uuid4()

    figure = component(
        doc_id=doc_id,
        component_type=ComponentType.FIGURE,
        visual_description="Diagrama com dois estados e transições.",
    )

    caption = component(
        doc_id=doc_id,
        component_type=ComponentType.FIGURE_CAPTION,
        text_extracted="Figura 1 – Cadeia de Markov.",
        parent_component_id=figure.component_id,
    )

    result = build_indexable_text(
        figure,
        [
            figure,
            caption,
        ],
    )

    assert result == (
        "Figure caption: Figura 1 – Cadeia de Markov.\n"
        "Visual description: Diagrama com dois estados e transições."
    )


def test_serializes_table_with_header_cell_relationships():
    table = TableStructure(
        header=(
            "Critério",
            "EDGAR",
        ),
        rows=(
            (
                "Suporte visual",
                "Sim",
            ),
            (
                "Requer OCR",
                "Seletivo",
            ),
        ),
    )

    assert table_structure_to_text(table) == (
        "Columns: Critério | EDGAR\n"
        "Row 1: Critério = Suporte visual | EDGAR = Sim\n"
        "Row 2: Critério = Requer OCR | EDGAR = Seletivo"
    )


def test_builds_table_representation_with_context_and_structure():
    doc_id = uuid4()

    structure = TableStructure(
        header=(
            "Critério",
            "EDGAR",
        ),
        rows=(
            (
                "Suporte visual",
                "Sim",
            ),
        ),
    )

    table = component(
        doc_id=doc_id,
        component_type=ComponentType.TABLE,
        table_structure=structure,
        visual_description="Tabela comparativa de sistemas.",
    )

    caption = component(
        doc_id=doc_id,
        component_type=ComponentType.TABLE_CAPTION,
        text_extracted="Tabela 1 – Trabalhos relacionados.",
        parent_component_id=table.component_id,
    )

    footnote = component(
        doc_id=doc_id,
        component_type=ComponentType.TABLE_FOOTNOTE,
        text_extracted="Fonte: Elaborado pelo autor.",
        parent_component_id=table.component_id,
    )

    result = build_indexable_text(
        table,
        [
            table,
            caption,
            footnote,
        ],
    )

    assert result == (
        "Table caption: Tabela 1 – Trabalhos relacionados.\n"
        "Table footnote: Fonte: Elaborado pelo autor.\n"
        "Columns: Critério | EDGAR\n"
        "Row 1: Critério = Suporte visual | EDGAR = Sim\n"
        "Visual description: Tabela comparativa de sistemas."
    )


def test_does_not_index_abandon_or_formula_yet():
    doc_id = uuid4()

    abandon = component(
        doc_id=doc_id,
        component_type=ComponentType.ABANDON,
        text_extracted="ignorar",
    )

    formula = component(
        doc_id=doc_id,
        component_type=ComponentType.ISOLATE_FORMULA,
        text_extracted="E = mc²",
    )

    assert (
        build_indexable_text(
            abandon,
            [abandon],
        )
        is None
    )

    assert (
        build_indexable_text(
            formula,
            [formula],
        )
        is None
    )
