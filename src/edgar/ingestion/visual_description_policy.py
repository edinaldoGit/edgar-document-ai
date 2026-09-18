from edgar.domain import ComponentType, DocumentComponent


def requires_visual_description(
    component: DocumentComponent,
) -> bool:
    if component.component_type == ComponentType.FIGURE:
        return True

    if component.component_type == ComponentType.TABLE:
        return component.table_structure is None

    return False
