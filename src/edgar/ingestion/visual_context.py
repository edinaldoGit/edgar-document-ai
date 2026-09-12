from edgar.domain import ComponentType, DocumentComponent


def build_visual_text_context(
    component: DocumentComponent,
    components: list[DocumentComponent],
) -> str | None:
    if component.component_type == ComponentType.FIGURE:
        allowed_child_types = {
            ComponentType.FIGURE_CAPTION,
        }
    elif component.component_type == ComponentType.TABLE:
        allowed_child_types = {
            ComponentType.TABLE_CAPTION,
            ComponentType.TABLE_FOOTNOTE,
        }
    else:
        raise ValueError("Visual text context is supported only for figures and tables.")

    related = [
        child
        for child in components
        if child.parent_component_id == component.component_id
        and child.component_type in allowed_child_types
        and child.text_extracted
    ]

    if not related:
        return None

    type_order = {
        ComponentType.FIGURE_CAPTION: 0,
        ComponentType.TABLE_CAPTION: 0,
        ComponentType.TABLE_FOOTNOTE: 1,
    }

    related.sort(
        key=lambda child: (
            type_order[child.component_type],
            child.bbox.y1,
            child.bbox.x1,
        )
    )

    labels = {
        ComponentType.FIGURE_CAPTION: "Figure caption",
        ComponentType.TABLE_CAPTION: "Table caption",
        ComponentType.TABLE_FOOTNOTE: "Table footnote",
    }

    return "\n".join(f"{labels[child.component_type]}: {child.text_extracted}" for child in related)
