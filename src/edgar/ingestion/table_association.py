from edgar.domain import ComponentType, DocumentComponent
from edgar.ingestion.spatial_relations import (
    horizontal_overlap_ratio,
    vertical_gap_pixels,
)


def find_table_for_footnote(
    footnote: DocumentComponent,
    components: list[DocumentComponent],
    *,
    min_horizontal_overlap: float = 0.5,
    max_vertical_gap_ratio: float = 3.0,
) -> DocumentComponent | None:
    if footnote.component_type != ComponentType.TABLE_FOOTNOTE:
        raise ValueError("Component must be a table footnote.")

    if not 0.0 <= min_horizontal_overlap <= 1.0:
        raise ValueError("Minimum horizontal overlap must be between 0 and 1.")

    if max_vertical_gap_ratio < 0:
        raise ValueError("Maximum vertical gap ratio must not be negative.")

    max_vertical_gap = footnote.bbox.height * max_vertical_gap_ratio

    candidates: list[tuple[int, float, DocumentComponent]] = []

    for component in components:
        if component.component_type != ComponentType.TABLE:
            continue

        if component.doc_id != footnote.doc_id:
            continue

        if component.page_index != footnote.page_index:
            continue

        if component.bbox.y2 > footnote.bbox.y1:
            continue

        overlap = horizontal_overlap_ratio(
            component.bbox,
            footnote.bbox,
        )

        if overlap < min_horizontal_overlap:
            continue

        vertical_gap = vertical_gap_pixels(
            component.bbox,
            footnote.bbox,
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


def associate_table_footnotes(
    components: list[DocumentComponent],
    *,
    min_horizontal_overlap: float = 0.5,
    max_vertical_gap_ratio: float = 3.0,
) -> list[DocumentComponent]:
    for footnote in components:
        if footnote.component_type != ComponentType.TABLE_FOOTNOTE:
            continue

        table = find_table_for_footnote(
            footnote,
            components,
            min_horizontal_overlap=min_horizontal_overlap,
            max_vertical_gap_ratio=max_vertical_gap_ratio,
        )

        if table is not None:
            footnote.parent_component_id = table.component_id

    return components
