from uuid import uuid4

import pytest

from edgar.domain import BoundingBox, ComponentType, DocumentComponent
from edgar.ingestion.caption_association import find_formula_for_caption


def make_component(doc_id, component_type, bbox, page_index=0):
    return DocumentComponent(
        doc_id=doc_id,
        page_index=page_index,
        component_type=component_type,
        bbox=bbox,
    )


def test_finds_formula_for_real_caption_geometry():
    doc_id = uuid4()

    formula = make_component(
        doc_id,
        ComponentType.ISOLATE_FORMULA,
        BoundingBox(
            x1=320,
            y1=332,
            x2=917,
            y2=413,
        ),
    )

    caption = make_component(
        doc_id,
        ComponentType.FORMULA_CAPTION,
        BoundingBox(
            x1=1007,
            y1=357,
            x2=1057,
            y2=391,
        ),
    )

    match = find_formula_for_caption(
        caption,
        [formula, caption],
    )

    assert match is formula


def test_prefers_closest_valid_formula():
    doc_id = uuid4()

    farther = make_component(
        doc_id,
        ComponentType.ISOLATE_FORMULA,
        BoundingBox(
            x1=100,
            y1=100,
            x2=300,
            y2=150,
        ),
    )

    closer = make_component(
        doc_id,
        ComponentType.ISOLATE_FORMULA,
        BoundingBox(
            x1=200,
            y1=100,
            x2=380,
            y2=150,
        ),
    )

    caption = make_component(
        doc_id,
        ComponentType.FORMULA_CAPTION,
        BoundingBox(
            x1=400,
            y1=110,
            x2=450,
            y2=140,
        ),
    )

    match = find_formula_for_caption(
        caption,
        [farther, closer, caption],
        max_horizontal_gap_ratio=10.0,
    )

    assert match is closer


def test_ignores_formula_without_enough_vertical_overlap():
    doc_id = uuid4()

    formula = make_component(
        doc_id,
        ComponentType.ISOLATE_FORMULA,
        BoundingBox(
            x1=100,
            y1=10,
            x2=300,
            y2=50,
        ),
    )

    caption = make_component(
        doc_id,
        ComponentType.FORMULA_CAPTION,
        BoundingBox(
            x1=320,
            y1=100,
            x2=370,
            y2=130,
        ),
    )

    assert find_formula_for_caption(caption, [formula]) is None


def test_ignores_formula_to_right_of_caption():
    doc_id = uuid4()

    caption = make_component(
        doc_id,
        ComponentType.FORMULA_CAPTION,
        BoundingBox(
            x1=100,
            y1=100,
            x2=150,
            y2=130,
        ),
    )

    formula = make_component(
        doc_id,
        ComponentType.ISOLATE_FORMULA,
        BoundingBox(
            x1=170,
            y1=90,
            x2=350,
            y2=140,
        ),
    )

    assert find_formula_for_caption(caption, [formula]) is None


def test_rejects_non_formula_caption():
    doc_id = uuid4()

    component = make_component(
        doc_id,
        ComponentType.PLAIN_TEXT,
        BoundingBox(
            x1=10,
            y1=10,
            x2=100,
            y2=30,
        ),
    )

    with pytest.raises(ValueError):
        find_formula_for_caption(component, [])
