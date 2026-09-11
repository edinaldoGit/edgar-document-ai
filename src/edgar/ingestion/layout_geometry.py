import math
from collections.abc import Sequence

from edgar.domain import BoundingBox


def detection_bbox_to_pixels(
    xyxy: Sequence[float],
    *,
    page_width: int,
    page_height: int,
) -> BoundingBox:
    if len(xyxy) != 4:
        raise ValueError("Detection bounding box must contain exactly four coordinates.")

    if page_width <= 0 or page_height <= 0:
        raise ValueError("Page dimensions must be positive.")

    if not all(math.isfinite(value) for value in xyxy):
        raise ValueError("Detection bounding box coordinates must be finite.")

    x1, y1, x2, y2 = xyxy

    pixel_x1 = max(0, math.floor(x1))
    pixel_y1 = max(0, math.floor(y1))
    pixel_x2 = min(page_width, math.ceil(x2))
    pixel_y2 = min(page_height, math.ceil(y2))

    return BoundingBox(
        x1=pixel_x1,
        y1=pixel_y1,
        x2=pixel_x2,
        y2=pixel_y2,
    )
