from edgar.domain import BoundingBox


def horizontal_overlap_pixels(
    first: BoundingBox,
    second: BoundingBox,
) -> int:
    return max(
        0,
        min(first.x2, second.x2) - max(first.x1, second.x1),
    )


def horizontal_overlap_ratio(
    first: BoundingBox,
    second: BoundingBox,
) -> float:
    overlap = horizontal_overlap_pixels(first, second)
    reference_width = min(first.width, second.width)

    return overlap / reference_width


def vertical_overlap_pixels(
    first: BoundingBox,
    second: BoundingBox,
) -> int:
    return max(
        0,
        min(first.y2, second.y2) - max(first.y1, second.y1),
    )


def vertical_overlap_ratio(
    first: BoundingBox,
    second: BoundingBox,
) -> float:
    overlap = vertical_overlap_pixels(first, second)
    reference_height = min(first.height, second.height)

    return overlap / reference_height


def horizontal_gap_pixels(
    first: BoundingBox,
    second: BoundingBox,
) -> int:
    if first.x2 < second.x1:
        return second.x1 - first.x2

    if second.x2 < first.x1:
        return first.x1 - second.x2

    return 0


def vertical_gap_pixels(
    first: BoundingBox,
    second: BoundingBox,
) -> int:
    if first.y2 < second.y1:
        return second.y1 - first.y2

    if second.y2 < first.y1:
        return first.y1 - second.y2

    return 0
