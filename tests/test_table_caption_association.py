from uuid import uuid4

import pytest

from edgar.domain import BoundingBox, ComponentType, DocumentComponent
from edgar.ingestion.caption_association import find_table_for_caption


def make_component(doc_id, component_type, bbox, page_index=0):
    return DocumentComponent(
        doc_id=doc_id,
        page_index=page_index,
        component_type=component_type,
        bbox=bbox,
    )


def test_finds_table_for_real_caption_geometry():
    doc_id = uuid4()

    table = make_component(
        doc_id,
        ComponentType.TABLE,
        BoundingBox(
            x1=351,
            y1=535,
            x2=2248,
            y2=982,
        ),
    )

    caption = make_component(
        doc_id,
        ComponentType.TABLE_CAPTION,
        BoundingBox(
            x1=350,
            y1=477,
            x2=1961,
            y2=533,
        ),
    )

    match = find_table_for_caption(
        caption,
        [table, caption],
    )

    assert match is table


def test_prefers_closest_valid_table():
    doc_id = uuid4()

    closer = make_component(
        doc_id,
        ComponentType.TABLE,
        BoundingBox(
            x1=100,
            y1=150,
            x2=400,
            y2=250,
        ),
    )

    farther = make_component(
        doc_id,
        ComponentType.TABLE,
        BoundingBox(
            x1=100,
            y1=300,
            x2=400,
            y2=400,
        ),
    )

    caption = make_component(
        doc_id,
        ComponentType.TABLE_CAPTION,
        BoundingBox(
            x1=100,
            y1=100,
            x2=400,
            y2=120,
        ),
    )

    match = find_table_for_caption(
        caption,
        [farther, closer, caption],
        max_vertical_gap_ratio=10.0,
    )

    assert match is closer


def test_ignores_table_above_caption():
    doc_id = uuid4()

    table = make_component(
        doc_id,
        ComponentType.TABLE,
        BoundingBox(
            x1=100,
            y1=50,
            x2=400,
            y2=90,
        ),
    )

    caption = make_component(
        doc_id,
        ComponentType.TABLE_CAPTION,
        BoundingBox(
            x1=100,
            y1=100,
            x2=400,
            y2=120,
        ),
    )

    assert find_table_for_caption(caption, [table]) is None


def test_ignores_table_without_enough_horizontal_overlap():
    doc_id = uuid4()

    caption = make_component(
        doc_id,
        ComponentType.TABLE_CAPTION,
        BoundingBox(
            x1=10,
            y1=10,
            x2=100,
            y2=30,
        ),
    )

    table = make_component(
        doc_id,
        ComponentType.TABLE,
        BoundingBox(
            x1=150,
            y1=35,
            x2=300,
            y2=100,
        ),
    )

    assert find_table_for_caption(caption, [table]) is None


def test_rejects_non_table_caption():
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
        find_table_for_caption(component, [])
