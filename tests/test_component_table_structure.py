from uuid import uuid4

from edgar.domain import (
    BoundingBox,
    ComponentType,
    DocumentComponent,
    TableStructure,
)


def test_component_has_no_table_structure_by_default():
    component = DocumentComponent(
        doc_id=uuid4(),
        page_index=0,
        component_type=ComponentType.TABLE,
        bbox=BoundingBox(
            x1=10,
            y1=20,
            x2=100,
            y2=200,
        ),
    )

    assert component.table_structure is None


def test_component_can_store_table_structure():
    table_structure = TableStructure(
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

    component = DocumentComponent(
        doc_id=uuid4(),
        page_index=0,
        component_type=ComponentType.TABLE,
        bbox=BoundingBox(
            x1=10,
            y1=20,
            x2=100,
            y2=200,
        ),
        table_structure=table_structure,
    )

    assert component.table_structure == table_structure
