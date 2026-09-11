import pytest

from edgar.domain.geometry import BoundingBox


def test_bounding_box_dimensions():
    bbox = BoundingBox(x1=10, y1=20, x2=110, y2=70)

    assert bbox.width == 100
    assert bbox.height == 50
    assert bbox.area == 5000


def test_bounding_box_centroid():
    bbox = BoundingBox(x1=10, y1=20, x2=110, y2=70)

    assert bbox.centroid == (60.0, 45.0)


def test_bounding_box_rejects_negative_coordinates():
    with pytest.raises(ValueError):
        BoundingBox(x1=-1, y1=0, x2=100, y2=100)


def test_bounding_box_rejects_invalid_horizontal_bounds():
    with pytest.raises(ValueError):
        BoundingBox(x1=100, y1=0, x2=100, y2=50)


def test_bounding_box_rejects_invalid_vertical_bounds():
    with pytest.raises(ValueError):
        BoundingBox(x1=0, y1=50, x2=100, y2=20)
