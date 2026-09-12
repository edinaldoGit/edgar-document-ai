import pytest

from edgar.domain import BoundingBox
from edgar.ingestion.pdf_geometry import bbox_pixels_to_page_points


def test_converts_full_rasterized_page_to_pdf_points():
    bbox = BoundingBox(
        x1=0,
        y1=0,
        x2=2481,
        y2=3508,
    )

    result = bbox_pixels_to_page_points(
        bbox,
        pixel_width=2481,
        pixel_height=3508,
        page_width_points=595.44,
        page_height_points=841.68,
    )

    assert result == pytest.approx(
        (
            0.0,
            0.0,
            595.44,
            841.68,
        )
    )


def test_converts_component_bbox_proportionally():
    bbox = BoundingBox(
        x1=620,
        y1=877,
        x2=1240,
        y2=1754,
    )

    x1, y1, x2, y2 = bbox_pixels_to_page_points(
        bbox,
        pixel_width=2480,
        pixel_height=3508,
        page_width_points=595.2,
        page_height_points=841.92,
    )

    assert x1 == pytest.approx(148.8)
    assert y1 == pytest.approx(210.48)
    assert x2 == pytest.approx(297.6)
    assert y2 == pytest.approx(420.96)


@pytest.mark.parametrize(
    ("pixel_width", "pixel_height"),
    [
        (0, 100),
        (100, 0),
        (-1, 100),
        (100, -1),
    ],
)
def test_rejects_invalid_pixel_dimensions(pixel_width, pixel_height):
    bbox = BoundingBox(
        x1=0,
        y1=0,
        x2=10,
        y2=10,
    )

    with pytest.raises(ValueError):
        bbox_pixels_to_page_points(
            bbox,
            pixel_width=pixel_width,
            pixel_height=pixel_height,
            page_width_points=100.0,
            page_height_points=100.0,
        )
