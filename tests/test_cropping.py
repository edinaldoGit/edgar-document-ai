from uuid import uuid4

import pytest
from PIL import Image

from edgar.domain import BoundingBox, ComponentType, DocumentComponent, DocumentPage
from edgar.ingestion.cropping import ComponentCropper


def test_crop_saves_component_image_and_sets_crop_ref(tmp_path):
    doc_id = uuid4()

    page_ref = f"documents/{doc_id}/pages/page_0001.png"
    page_path = tmp_path / page_ref
    page_path.parent.mkdir(parents=True)

    Image.new("RGB", (100, 80), "white").save(page_path)

    page = DocumentPage(
        doc_id=doc_id,
        page_index=0,
        width=100,
        height=80,
        render_dpi=300,
        image_ref=page_ref,
    )

    component = DocumentComponent(
        doc_id=doc_id,
        page_index=0,
        component_type=ComponentType.FIGURE,
        bbox=BoundingBox(
            x1=10,
            y1=20,
            x2=40,
            y2=50,
        ),
    )

    cropper = ComponentCropper(storage_root=tmp_path)

    result = cropper.crop(page, component)

    expected_ref = f"documents/{doc_id}/crops/page_0001/{component.component_id}.png"

    assert result is component
    assert component.crop_ref == expected_ref

    crop_path = tmp_path / expected_ref
    assert crop_path.is_file()

    with Image.open(crop_path) as crop:
        assert crop.size == (30, 30)


def test_crop_rejects_component_from_different_document(tmp_path):
    page = DocumentPage(
        doc_id=uuid4(),
        page_index=0,
        width=100,
        height=80,
        render_dpi=300,
        image_ref="page.png",
    )

    component = DocumentComponent(
        doc_id=uuid4(),
        page_index=0,
        component_type=ComponentType.FIGURE,
        bbox=BoundingBox(
            x1=10,
            y1=10,
            x2=20,
            y2=20,
        ),
    )

    cropper = ComponentCropper(storage_root=tmp_path)

    with pytest.raises(ValueError):
        cropper.crop(page, component)


def test_crop_rejects_component_from_different_page(tmp_path):
    doc_id = uuid4()

    page = DocumentPage(
        doc_id=doc_id,
        page_index=0,
        width=100,
        height=80,
        render_dpi=300,
        image_ref="page.png",
    )

    component = DocumentComponent(
        doc_id=doc_id,
        page_index=1,
        component_type=ComponentType.FIGURE,
        bbox=BoundingBox(
            x1=10,
            y1=10,
            x2=20,
            y2=20,
        ),
    )

    cropper = ComponentCropper(storage_root=tmp_path)

    with pytest.raises(ValueError):
        cropper.crop(page, component)


def test_crop_rejects_page_image_dimension_mismatch(tmp_path):
    image_path = tmp_path / "page.png"
    Image.new("RGB", (90, 80), "white").save(image_path)

    doc_id = uuid4()

    page = DocumentPage(
        doc_id=doc_id,
        page_index=0,
        width=100,
        height=80,
        render_dpi=300,
        image_ref="page.png",
    )

    component = DocumentComponent(
        doc_id=doc_id,
        page_index=0,
        component_type=ComponentType.FIGURE,
        bbox=BoundingBox(
            x1=10,
            y1=10,
            x2=20,
            y2=20,
        ),
    )

    cropper = ComponentCropper(storage_root=tmp_path)

    with pytest.raises(RuntimeError):
        cropper.crop(page, component)
