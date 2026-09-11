from uuid import uuid4

from edgar.domain import BoundingBox, ComponentType, DocumentComponent
from edgar.ingestion.caption_association import associate_formula_captions


def test_associate_formula_caption_sets_parent_component_id():
    doc_id = uuid4()

    formula = DocumentComponent(
        doc_id=doc_id,
        page_index=0,
        component_type=ComponentType.ISOLATE_FORMULA,
        bbox=BoundingBox(
            x1=320,
            y1=332,
            x2=917,
            y2=413,
        ),
    )

    caption = DocumentComponent(
        doc_id=doc_id,
        page_index=0,
        component_type=ComponentType.FORMULA_CAPTION,
        bbox=BoundingBox(
            x1=1007,
            y1=357,
            x2=1057,
            y2=391,
        ),
    )

    components = [formula, caption]

    result = associate_formula_captions(components)

    assert result is components
    assert caption.parent_component_id == formula.component_id
    assert formula.parent_component_id is None


def test_unmatched_formula_caption_keeps_parent_empty():
    doc_id = uuid4()

    caption = DocumentComponent(
        doc_id=doc_id,
        page_index=0,
        component_type=ComponentType.FORMULA_CAPTION,
        bbox=BoundingBox(
            x1=100,
            y1=100,
            x2=150,
            y2=130,
        ),
    )

    associate_formula_captions([caption])

    assert caption.parent_component_id is None
