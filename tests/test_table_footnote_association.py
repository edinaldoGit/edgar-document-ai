from uuid import uuid4

import pytest

from edgar.domain import BoundingBox, ComponentType, DocumentComponent
from edgar.ingestion.table_association import find_table_for_footnote


def make_component(doc_id, component_type, bbox, page_index=0):
    return DocumentComponent(
        doc_id=doc_id,
        page_index=page_index,
        component_type=component_type,
        bbox=bbox,
    )


def test_finds_table_for_real_footnote_geometry():
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
        page_index=28,
    )

    footnote = make_component(
        doc_id,
        ComponentType.TABLE_FOOTNOTE,
        BoundingBox(
            x1=349,
            y1=984,
            x2=829,
            y2=1031,
        ),
        page_index=28,
    )

    match = find_table_for_footnote(
        footnote,
        [table, footnote],
    )

    assert match is table


def test_prefers_closest_valid_table():
    doc_id = uuid4()

    farther = make_component(
        doc_id,
        ComponentType.TABLE,
        BoundingBox(
            x1=100,
            y1=100,
            x2=400,
            y2=200,
        ),
    )

    closer = make_component(
        doc_id,
        ComponentType.TABLE,
        BoundingBox(
            x1=100,
            y1=230,
            x2=400,
            y2=300,
        ),
    )

    footnote = make_component(
        doc_id,
        ComponentType.TABLE_FOOTNOTE,
        BoundingBox(
            x1=100,
            y1=320,
            x2=250,
            y2=340,
        ),
    )

    match = find_table_for_footnote(
        footnote,
        [farther, closer, footnote],
        max_vertical_gap_ratio=10.0,
    )

    assert match is closer


def test_ignores_table_below_footnote():
    doc_id = uuid4()

    footnote = make_component(
        doc_id,
        ComponentType.TABLE_FOOTNOTE,
        BoundingBox(
            x1=100,
            y1=100,
            x2=250,
            y2=130,
        ),
    )

    table = make_component(
        doc_id,
        ComponentType.TABLE,
        BoundingBox(
            x1=100,
            y1=140,
            x2=400,
            y2=250,
        ),
    )

    assert find_table_for_footnote(footnote, [table]) is None


def test_ignores_table_without_enough_horizontal_overlap():
    doc_id = uuid4()

    table = make_component(
        doc_id,
        ComponentType.TABLE,
        BoundingBox(
            x1=10,
            y1=10,
            x2=100,
            y2=100,
        ),
    )

    footnote = make_component(
        doc_id,
        ComponentType.TABLE_FOOTNOTE,
        BoundingBox(
            x1=150,
            y1=110,
            x2=250,
            y2=140,
        ),
    )

    assert find_table_for_footnote(footnote, [table]) is None


def test_rejects_non_table_footnote():
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
        find_table_for_footnote(component, [])
