from uuid import uuid4

import pytest

from edgar.domain import BoundingBox, ComponentType, DocumentComponent
from edgar.ingestion.caption_association import find_figure_for_caption


def make_component(doc_id, component_type, bbox, page_index=0):
    return DocumentComponent(
        doc_id=doc_id,
        page_index=page_index,
        component_type=component_type,
        bbox=bbox,
    )


def test_finds_figure_for_real_caption_geometry():
    doc_id = uuid4()

    figure = make_component(
        doc_id,
        ComponentType.FIGURE,
        BoundingBox(
            x1=466,
            y1=1068,
            x2=754,
            y2=1259,
        ),
    )

    caption = make_component(
        doc_id,
        ComponentType.FIGURE_CAPTION,
        BoundingBox(
            x1=384,
            y1=1276,
            x2=833,
            y2=1309,
        ),
    )

    match = find_figure_for_caption(
        caption,
        [figure, caption],
    )

    assert match is figure


def test_prefers_closest_valid_figure():
    doc_id = uuid4()

    farther = make_component(
        doc_id,
        ComponentType.FIGURE,
        BoundingBox(
            x1=100,
            y1=100,
            x2=300,
            y2=200,
        ),
    )

    closer = make_component(
        doc_id,
        ComponentType.FIGURE,
        BoundingBox(
            x1=100,
            y1=230,
            x2=300,
            y2=300,
        ),
    )

    caption = make_component(
        doc_id,
        ComponentType.FIGURE_CAPTION,
        BoundingBox(
            x1=100,
            y1=320,
            x2=300,
            y2=340,
        ),
    )

    match = find_figure_for_caption(
        caption,
        [farther, closer, caption],
        max_vertical_gap_ratio=10.0,
    )

    assert match is closer


def test_ignores_figure_without_enough_horizontal_overlap():
    doc_id = uuid4()

    figure = make_component(
        doc_id,
        ComponentType.FIGURE,
        BoundingBox(
            x1=10,
            y1=10,
            x2=100,
            y2=100,
        ),
    )

    caption = make_component(
        doc_id,
        ComponentType.FIGURE_CAPTION,
        BoundingBox(
            x1=150,
            y1=110,
            x2=250,
            y2=130,
        ),
    )

    assert find_figure_for_caption(caption, [figure]) is None


def test_ignores_figure_below_caption():
    doc_id = uuid4()

    caption = make_component(
        doc_id,
        ComponentType.FIGURE_CAPTION,
        BoundingBox(
            x1=100,
            y1=100,
            x2=300,
            y2=120,
        ),
    )

    figure = make_component(
        doc_id,
        ComponentType.FIGURE,
        BoundingBox(
            x1=100,
            y1=130,
            x2=300,
            y2=230,
        ),
    )

    assert find_figure_for_caption(caption, [figure]) is None


def test_rejects_non_figure_caption():
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
        find_figure_for_caption(component, [])
