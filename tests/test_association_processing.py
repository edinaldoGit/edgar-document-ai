from uuid import uuid4

from edgar.domain import (
    BoundingBox,
    ComponentType,
    DocumentComponent,
    DocumentPage,
)
from edgar.ingestion.association_processing import (
    ComponentAssociationProcessor,
)


def component(
    *,
    doc_id,
    component_type,
    bbox,
):
    return DocumentComponent(
        doc_id=doc_id,
        page_index=0,
        component_type=component_type,
        bbox=bbox,
    )


def test_associates_related_components_by_geometry():
    doc_id = uuid4()

    page = DocumentPage(
        doc_id=doc_id,
        page_index=0,
        width=1200,
        height=1600,
        render_dpi=300,
        image_ref="page.png",
    )

    figure = component(
        doc_id=doc_id,
        component_type=ComponentType.FIGURE,
        bbox=BoundingBox(
            x1=100,
            y1=100,
            x2=300,
            y2=300,
        ),
    )

    figure_caption = component(
        doc_id=doc_id,
        component_type=ComponentType.FIGURE_CAPTION,
        bbox=BoundingBox(
            x1=120,
            y1=310,
            x2=280,
            y2=340,
        ),
    )

    formula = component(
        doc_id=doc_id,
        component_type=ComponentType.ISOLATE_FORMULA,
        bbox=BoundingBox(
            x1=100,
            y1=500,
            x2=300,
            y2=560,
        ),
    )

    formula_caption = component(
        doc_id=doc_id,
        component_type=ComponentType.FORMULA_CAPTION,
        bbox=BoundingBox(
            x1=310,
            y1=510,
            x2=350,
            y2=540,
        ),
    )

    table = component(
        doc_id=doc_id,
        component_type=ComponentType.TABLE,
        bbox=BoundingBox(
            x1=500,
            y1=100,
            x2=900,
            y2=300,
        ),
    )

    table_caption = component(
        doc_id=doc_id,
        component_type=ComponentType.TABLE_CAPTION,
        bbox=BoundingBox(
            x1=520,
            y1=60,
            x2=880,
            y2=90,
        ),
    )

    table_footnote = component(
        doc_id=doc_id,
        component_type=ComponentType.TABLE_FOOTNOTE,
        bbox=BoundingBox(
            x1=520,
            y1=310,
            x2=700,
            y2=340,
        ),
    )

    components = [
        figure,
        figure_caption,
        formula,
        formula_caption,
        table,
        table_caption,
        table_footnote,
    ]

    processor = ComponentAssociationProcessor()

    result = processor.process(
        page,
        components,
    )

    assert result == components

    assert figure_caption.parent_component_id == figure.component_id
    assert formula_caption.parent_component_id == formula.component_id
    assert table_caption.parent_component_id == table.component_id
    assert table_footnote.parent_component_id == table.component_id
