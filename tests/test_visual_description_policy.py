from uuid import uuid4

import pytest

from edgar.domain import BoundingBox, ComponentType, DocumentComponent
from edgar.ingestion.visual_description_policy import (
    requires_visual_description,
)


def make_component(component_type):
    return DocumentComponent(
        doc_id=uuid4(),
        page_index=0,
        component_type=component_type,
        bbox=BoundingBox(
            x1=0,
            y1=0,
            x2=10,
            y2=10,
        ),
    )


@pytest.mark.parametrize(
    "component_type",
    [
        ComponentType.FIGURE,
        ComponentType.TABLE,
    ],
)
def test_visual_components_require_description(component_type):
    component = make_component(component_type)

    assert requires_visual_description(component)


@pytest.mark.parametrize(
    "component_type",
    [
        ComponentType.PLAIN_TEXT,
        ComponentType.TITLE,
        ComponentType.ISOLATE_FORMULA,
        ComponentType.FIGURE_CAPTION,
        ComponentType.TABLE_CAPTION,
        ComponentType.TABLE_FOOTNOTE,
        ComponentType.FORMULA_CAPTION,
        ComponentType.ABANDON,
        ComponentType.OTHER,
    ],
)
def test_other_components_do_not_require_visual_description(component_type):
    component = make_component(component_type)

    assert not requires_visual_description(component)
