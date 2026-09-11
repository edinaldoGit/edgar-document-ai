import pytest

from edgar.domain import BoundingBox
from edgar.ingestion.spatial_relations import (
    horizontal_gap_pixels,
    horizontal_overlap_pixels,
    horizontal_overlap_ratio,
    vertical_gap_pixels,
    vertical_overlap_pixels,
    vertical_overlap_ratio,
)


def test_real_figure_and_caption_have_expected_spatial_relation():
    figure = BoundingBox(
        x1=466,
        y1=1068,
        x2=754,
        y2=1259,
    )

    caption = BoundingBox(
        x1=384,
        y1=1276,
        x2=833,
        y2=1309,
    )

    assert horizontal_overlap_pixels(figure, caption) == 288
    assert horizontal_overlap_ratio(figure, caption) == pytest.approx(1.0)
    assert vertical_gap_pixels(figure, caption) == 17


def test_real_formula_and_caption_have_expected_spatial_relation():
    formula = BoundingBox(
        x1=320,
        y1=332,
        x2=917,
        y2=413,
    )

    caption = BoundingBox(
        x1=1007,
        y1=357,
        x2=1057,
        y2=391,
    )

    assert vertical_overlap_pixels(formula, caption) == 34
    assert vertical_overlap_ratio(formula, caption) == pytest.approx(1.0)
    assert horizontal_gap_pixels(formula, caption) == 90


def test_boxes_without_horizontal_overlap_have_zero_overlap():
    first = BoundingBox(
        x1=10,
        y1=10,
        x2=20,
        y2=20,
    )

    second = BoundingBox(
        x1=30,
        y1=30,
        x2=40,
        y2=40,
    )

    assert horizontal_overlap_pixels(first, second) == 0
    assert horizontal_overlap_ratio(first, second) == 0.0


def test_boxes_without_vertical_overlap_have_zero_overlap():
    first = BoundingBox(
        x1=10,
        y1=10,
        x2=20,
        y2=20,
    )

    second = BoundingBox(
        x1=10,
        y1=30,
        x2=20,
        y2=40,
    )

    assert vertical_overlap_pixels(first, second) == 0
    assert vertical_overlap_ratio(first, second) == 0.0


def test_horizontally_overlapping_boxes_have_zero_gap():
    first = BoundingBox(
        x1=10,
        y1=10,
        x2=30,
        y2=30,
    )

    second = BoundingBox(
        x1=20,
        y1=40,
        x2=40,
        y2=50,
    )

    assert horizontal_gap_pixels(first, second) == 0


def test_vertically_overlapping_boxes_have_zero_gap():
    first = BoundingBox(
        x1=10,
        y1=10,
        x2=30,
        y2=30,
    )

    second = BoundingBox(
        x1=20,
        y1=20,
        x2=40,
        y2=40,
    )

    assert vertical_gap_pixels(first, second) == 0


def test_horizontal_gap_is_symmetric():
    left = BoundingBox(
        x1=10,
        y1=10,
        x2=20,
        y2=30,
    )

    right = BoundingBox(
        x1=35,
        y1=10,
        x2=45,
        y2=30,
    )

    assert horizontal_gap_pixels(left, right) == 15
    assert horizontal_gap_pixels(right, left) == 15


def test_vertical_gap_is_symmetric():
    upper = BoundingBox(
        x1=10,
        y1=10,
        x2=30,
        y2=20,
    )

    lower = BoundingBox(
        x1=10,
        y1=35,
        x2=30,
        y2=45,
    )

    assert vertical_gap_pixels(upper, lower) == 15
    assert vertical_gap_pixels(lower, upper) == 15
