from edgar.domain import ComponentType, DocumentComponent
from edgar.ingestion.spatial_relations import (
    horizontal_gap_pixels,
    horizontal_overlap_ratio,
    vertical_gap_pixels,
    vertical_overlap_ratio,
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


def find_formula_for_caption(
    caption: DocumentComponent,
    components: list[DocumentComponent],
    *,
    min_vertical_overlap: float = 0.5,
    max_horizontal_gap_ratio: float = 3.0,
) -> DocumentComponent | None:
    if caption.component_type != ComponentType.FORMULA_CAPTION:
        raise ValueError("Component must be a formula caption.")

    if not 0.0 <= min_vertical_overlap <= 1.0:
        raise ValueError("Minimum vertical overlap must be between 0 and 1.")

    if max_horizontal_gap_ratio < 0:
        raise ValueError("Maximum horizontal gap ratio must not be negative.")

    max_horizontal_gap = caption.bbox.width * max_horizontal_gap_ratio

    candidates: list[tuple[int, float, DocumentComponent]] = []

    for component in components:
        if component.component_type != ComponentType.ISOLATE_FORMULA:
            continue

        if component.doc_id != caption.doc_id:
            continue

        if component.page_index != caption.page_index:
            continue

        if component.bbox.x2 > caption.bbox.x1:
            continue

        overlap = vertical_overlap_ratio(
            component.bbox,
            caption.bbox,
        )

        if overlap < min_vertical_overlap:
            continue

        horizontal_gap = horizontal_gap_pixels(
            component.bbox,
            caption.bbox,
        )

        if horizontal_gap > max_horizontal_gap:
            continue

        candidates.append(
            (
                horizontal_gap,
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


def associate_formula_captions(
    components: list[DocumentComponent],
    *,
    min_vertical_overlap: float = 0.5,
    max_horizontal_gap_ratio: float = 3.0,
) -> list[DocumentComponent]:
    for caption in components:
        if caption.component_type != ComponentType.FORMULA_CAPTION:
            continue

        formula = find_formula_for_caption(
            caption,
            components,
            min_vertical_overlap=min_vertical_overlap,
            max_horizontal_gap_ratio=max_horizontal_gap_ratio,
        )

        if formula is not None:
            caption.parent_component_id = formula.component_id

    return components
