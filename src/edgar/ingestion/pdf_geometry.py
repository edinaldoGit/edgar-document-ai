from edgar.domain import BoundingBox


def bbox_pixels_to_page_points(
    bbox: BoundingBox,
    *,
    pixel_width: int,
    pixel_height: int,
    page_width_points: float,
    page_height_points: float,
) -> tuple[float, float, float, float]:
    if pixel_width <= 0 or pixel_height <= 0:
        raise ValueError("Pixel dimensions must be positive.")

    if page_width_points <= 0 or page_height_points <= 0:
        raise ValueError("PDF page dimensions must be positive.")

    scale_x = page_width_points / pixel_width
    scale_y = page_height_points / pixel_height

    return (
        bbox.x1 * scale_x,
        bbox.y1 * scale_y,
        bbox.x2 * scale_x,
        bbox.y2 * scale_y,
    )
