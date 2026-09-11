from uuid import uuid4

import pytest

from edgar.domain import BoundingBox, ComponentType, DocumentComponent
from edgar.ingestion.cropping_policy import requires_visual_crop


@pytest.mark.parametrize(
    "component_type",
    [
        ComponentType.FIGURE,
        ComponentType.TABLE,
        ComponentType.ISOLATE_FORMULA,
    ],
)
def test_visual_components_require_crop(component_type):
    component = DocumentComponent(
        doc_id=uuid4(),
        page_index=0,
        component_type=component_type,
        bbox=BoundingBox(x1=0, y1=0, x2=10, y2=10),
    )

    assert requires_visual_crop(component)


@pytest.mark.parametrize(
    "component_type",
    [
        ComponentType.PLAIN_TEXT,
        ComponentType.TITLE,
        ComponentType.FIGURE_CAPTION,
        ComponentType.TABLE_CAPTION,
        ComponentType.TABLE_FOOTNOTE,
        ComponentType.FORMULA_CAPTION,
        ComponentType.ABANDON,
        ComponentType.OTHER,
    ],
)
def test_non_visual_components_do_not_require_crop(component_type):
    component = DocumentComponent(
        doc_id=uuid4(),
        page_index=0,
        component_type=component_type,
        bbox=BoundingBox(x1=0, y1=0, x2=10, y2=10),
    )

    assert not requires_visual_crop(component)
