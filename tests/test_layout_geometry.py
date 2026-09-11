import pytest

from edgar.domain import BoundingBox
from edgar.ingestion.layout_geometry import detection_bbox_to_pixels


def test_detection_bbox_expands_fractional_coordinates_outward():
    bbox = detection_bbox_to_pixels(
        [10.8, 20.2, 30.1, 40.01],
        page_width=100,
        page_height=100,
    )

    assert bbox == BoundingBox(
        x1=10,
        y1=20,
        x2=31,
        y2=41,
    )


def test_detection_bbox_preserves_integer_coordinates():
    bbox = detection_bbox_to_pixels(
        [10.0, 20.0, 30.0, 40.0],
        page_width=100,
        page_height=100,
    )

    assert bbox == BoundingBox(
        x1=10,
        y1=20,
        x2=30,
        y2=40,
    )


def test_detection_bbox_is_clamped_to_page_bounds():
    bbox = detection_bbox_to_pixels(
        [-4.2, -2.1, 105.8, 120.4],
        page_width=100,
        page_height=80,
    )

    assert bbox == BoundingBox(
        x1=0,
        y1=0,
        x2=100,
        y2=80,
    )


@pytest.mark.parametrize(
    "xyxy",
    [
        [1.0, 2.0, 3.0],
        [1.0, 2.0, 3.0, 4.0, 5.0],
    ],
)
def test_detection_bbox_rejects_invalid_coordinate_count(xyxy):
    with pytest.raises(ValueError):
        detection_bbox_to_pixels(
            xyxy,
            page_width=100,
            page_height=100,
        )


@pytest.mark.parametrize(
    "xyxy",
    [
        [float("nan"), 0.0, 10.0, 10.0],
        [0.0, float("inf"), 10.0, 10.0],
    ],
)
def test_detection_bbox_rejects_non_finite_coordinates(xyxy):
    with pytest.raises(ValueError):
        detection_bbox_to_pixels(
            xyxy,
            page_width=100,
            page_height=100,
        )


@pytest.mark.parametrize(
    ("page_width", "page_height"),
    [
        (0, 100),
        (100, 0),
        (-1, 100),
        (100, -1),
    ],
)
def test_detection_bbox_rejects_invalid_page_dimensions(page_width, page_height):
    with pytest.raises(ValueError):
        detection_bbox_to_pixels(
            [10.0, 10.0, 20.0, 20.0],
            page_width=page_width,
            page_height=page_height,
        )
