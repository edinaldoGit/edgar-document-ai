from edgar.domain import ComponentType, DocumentComponent

VISUAL_DESCRIPTION_TYPES = frozenset(
    {
        ComponentType.FIGURE,
        ComponentType.TABLE,
    }
)


def requires_visual_description(
    component: DocumentComponent,
) -> bool:
    return component.component_type in VISUAL_DESCRIPTION_TYPES
