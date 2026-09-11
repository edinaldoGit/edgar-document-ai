from edgar.domain import ComponentType, DocumentComponent

VISUAL_CROP_TYPES = frozenset(
    {
        ComponentType.FIGURE,
        ComponentType.TABLE,
        ComponentType.ISOLATE_FORMULA,
    }
)


def requires_visual_crop(component: DocumentComponent) -> bool:
    return component.component_type in VISUAL_CROP_TYPES
