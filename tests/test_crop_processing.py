from uuid import uuid4

from edgar.domain import (
    BoundingBox,
    ComponentType,
    DocumentComponent,
    DocumentPage,
)
from edgar.ingestion.crop_processing import VisualCropProcessor


class RecordingCropper:
    def __init__(self):
        self.cropped_component_ids = []

    def crop(self, page, component):
        self.cropped_component_ids.append(component.component_id)
        component.crop_ref = f"crop/{component.component_id}.png"
        return component


def make_component(doc_id, component_type):
    return DocumentComponent(
        doc_id=doc_id,
        page_index=0,
        component_type=component_type,
        bbox=BoundingBox(x1=10, y1=10, x2=20, y2=20),
    )


def test_process_crops_only_visual_components():
    doc_id = uuid4()

    page = DocumentPage(
        doc_id=doc_id,
        page_index=0,
        width=100,
        height=100,
        render_dpi=300,
        image_ref="page.png",
    )

    plain_text = make_component(doc_id, ComponentType.PLAIN_TEXT)
    figure = make_component(doc_id, ComponentType.FIGURE)
    table = make_component(doc_id, ComponentType.TABLE)
    formula = make_component(doc_id, ComponentType.ISOLATE_FORMULA)
    caption = make_component(doc_id, ComponentType.FIGURE_CAPTION)

    components = [
        plain_text,
        figure,
        table,
        formula,
        caption,
    ]

    cropper = RecordingCropper()
    processor = VisualCropProcessor(cropper=cropper)

    result = processor.process(page, components)

    assert result is components

    assert cropper.cropped_component_ids == [
        figure.component_id,
        table.component_id,
        formula.component_id,
    ]

    assert plain_text.crop_ref is None
    assert figure.crop_ref is not None
    assert table.crop_ref is not None
    assert formula.crop_ref is not None
    assert caption.crop_ref is None
