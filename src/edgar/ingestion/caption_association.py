from edgar.domain import ComponentType, DocumentComponent
from edgar.ingestion.spatial_relations import (
    horizontal_overlap_ratio,
    vertical_gap_pixels,
)


def find_figure_for_caption(
    caption: DocumentComponent,
    components: list[DocumentComponent],
    *,
    min_horizontal_overlap: float = 0.5,
    max_vertical_gap_ratio: float = 3.0,
) -> DocumentComponent | None:
    if caption.component_type != ComponentType.FIGURE_CAPTION:
        raise ValueError("Component must be a figure caption.")

    if not 0.0 <= min_horizontal_overlap <= 1.0:
        raise ValueError("Minimum horizontal overlap must be between 0 and 1.")

    if max_vertical_gap_ratio < 0:
        raise ValueError("Maximum vertical gap ratio must not be negative.")

    max_vertical_gap = caption.bbox.height * max_vertical_gap_ratio

    candidates: list[tuple[int, float, DocumentComponent]] = []

    for component in components:
        if component.component_type != ComponentType.FIGURE:
            continue

        if component.doc_id != caption.doc_id:
            continue

        if component.page_index != caption.page_index:
            continue

        if component.bbox.y2 > caption.bbox.y1:
            continue

        overlap = horizontal_overlap_ratio(
            component.bbox,
            caption.bbox,
        )

        if overlap < min_horizontal_overlap:
            continue

        vertical_gap = vertical_gap_pixels(
            component.bbox,
            caption.bbox,
        )

        if vertical_gap > max_vertical_gap:
            continue

        candidates.append(
            (
                vertical_gap,
                -overlap,
                component,
            )
        )

    if not candidates:
        return None

    candidates.sort(key=lambda candidate: (candidate[0], candidate[1]))

    return candidates[0][2]


def associate_figure_captions(
    components: list[DocumentComponent],
    *,
    min_horizontal_overlap: float = 0.5,
    max_vertical_gap_ratio: float = 3.0,
) -> list[DocumentComponent]:
    for caption in components:
        if caption.component_type != ComponentType.FIGURE_CAPTION:
            continue

        figure = find_figure_for_caption(
            caption,
            components,
            min_horizontal_overlap=min_horizontal_overlap,
            max_vertical_gap_ratio=max_vertical_gap_ratio,
        )

        if figure is not None:
            caption.parent_component_id = figure.component_id

    return components
