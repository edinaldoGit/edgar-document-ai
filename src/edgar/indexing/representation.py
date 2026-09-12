from edgar.domain import ComponentType, DocumentComponent, TableStructure
from edgar.ingestion.visual_context import build_visual_text_context


def table_structure_to_text(
    table_structure: TableStructure,
) -> str:
    lines = [
        "Columns: " + " | ".join(table_structure.header),
    ]

    for row_index, row in enumerate(
        table_structure.rows,
        start=1,
    ):
        cells = []

        for header, value in zip(
            table_structure.header,
            row,
            strict=True,
        ):
            if value is None:
                continue

            cells.append(f"{header} = {value}")

        if cells:
            lines.append(f"Row {row_index}: " + " | ".join(cells))

    return "\n".join(lines)


def build_indexable_text(
    component: DocumentComponent,
    components: list[DocumentComponent],
) -> str | None:
    if component.component_type in {
        ComponentType.ABANDON,
        ComponentType.ISOLATE_FORMULA,
    }:
        return None

    if component.component_type == ComponentType.FIGURE:
        parts = []

        context = build_visual_text_context(
            component,
            components,
        )

        if context:
            parts.append(context)

        if component.visual_description:
            parts.append(f"Visual description: {component.visual_description}")

        return _join_parts(parts)

    if component.component_type == ComponentType.TABLE:
        parts = []

        context = build_visual_text_context(
            component,
            components,
        )

        if context:
            parts.append(context)

        if component.table_structure:
            parts.append(
                table_structure_to_text(
                    component.table_structure,
                )
            )

        if component.visual_description:
            parts.append(f"Visual description: {component.visual_description}")

        return _join_parts(parts)

    if component.text_extracted:
        text = component.text_extracted.strip()

        if text:
            return text

    return None


def _join_parts(
    parts: list[str],
) -> str | None:
    cleaned = [part.strip() for part in parts if part.strip()]

    if not cleaned:
        return None

    return "\n".join(cleaned)
