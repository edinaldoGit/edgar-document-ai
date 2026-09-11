from uuid import uuid4

import pytest

from edgar.domain import BoundingBox, ComponentType, DocumentComponent


def test_document_component_creation():
    doc_id = uuid4()

    component = DocumentComponent(
        doc_id=doc_id,
        page_index=0,
        component_type=ComponentType.PLAIN_TEXT,
        bbox=BoundingBox(x1=10, y1=20, x2=110, y2=70),
        detection_confidence=0.95,
    )

    assert component.doc_id == doc_id
    assert component.page_index == 0
    assert component.page_number == 1
    assert component.component_type == ComponentType.PLAIN_TEXT
    assert component.detection_confidence == 0.95


def test_document_component_generates_component_id():
    component = DocumentComponent(
        doc_id=uuid4(),
        page_index=0,
        component_type=ComponentType.FIGURE,
        bbox=BoundingBox(x1=0, y1=0, x2=100, y2=100),
    )

    assert component.component_id is not None


def test_document_component_starts_without_enrichment():
    component = DocumentComponent(
        doc_id=uuid4(),
        page_index=0,
        component_type=ComponentType.TABLE,
        bbox=BoundingBox(x1=0, y1=0, x2=100, y2=100),
    )

    assert component.text_extracted is None
    assert component.visual_description is None
    assert component.crop_ref is None
    assert component.parent_component_id is None


def test_document_component_rejects_negative_page_index():
    with pytest.raises(ValueError):
        DocumentComponent(
            doc_id=uuid4(),
            page_index=-1,
            component_type=ComponentType.PLAIN_TEXT,
            bbox=BoundingBox(x1=0, y1=0, x2=100, y2=100),
        )


@pytest.mark.parametrize("confidence", [-0.1, 1.1])
def test_document_component_rejects_invalid_confidence(confidence):
    with pytest.raises(ValueError):
        DocumentComponent(
            doc_id=uuid4(),
            page_index=0,
            component_type=ComponentType.PLAIN_TEXT,
            bbox=BoundingBox(x1=0, y1=0, x2=100, y2=100),
            detection_confidence=confidence,
        )


def test_document_component_cannot_be_its_own_parent():
    component_id = uuid4()

    with pytest.raises(ValueError):
        DocumentComponent(
            component_id=component_id,
            doc_id=uuid4(),
            page_index=0,
            component_type=ComponentType.FIGURE_CAPTION,
            bbox=BoundingBox(x1=0, y1=0, x2=100, y2=100),
            parent_component_id=component_id,
        )
