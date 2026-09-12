from uuid import uuid4

import pytest

from edgar.domain import BoundingBox, ComponentType, DocumentComponent
from edgar.ingestion.text_extraction_policy import (
    requires_native_text_extraction,
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
        ComponentType.PLAIN_TEXT,
        ComponentType.TITLE,
        ComponentType.FIGURE_CAPTION,
        ComponentType.TABLE_CAPTION,
        ComponentType.TABLE_FOOTNOTE,
        ComponentType.FORMULA_CAPTION,
        ComponentType.OTHER,
    ],
)
def test_textual_components_attempt_native_text_extraction(component_type):
    component = make_component(component_type)

    assert requires_native_text_extraction(component)


@pytest.mark.parametrize(
    "component_type",
    [
        ComponentType.FIGURE,
        ComponentType.TABLE,
        ComponentType.ISOLATE_FORMULA,
        ComponentType.ABANDON,
    ],
)
def test_visual_or_discarded_components_skip_native_text_extraction(
    component_type,
):
    component = make_component(component_type)

    assert not requires_native_text_extraction(component)
