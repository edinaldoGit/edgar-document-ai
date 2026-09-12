from edgar.domain import ComponentType, DocumentComponent

NATIVE_TEXT_TYPES = frozenset(
    {
        ComponentType.PLAIN_TEXT,
        ComponentType.TITLE,
        ComponentType.FIGURE_CAPTION,
        ComponentType.TABLE_CAPTION,
        ComponentType.TABLE_FOOTNOTE,
        ComponentType.FORMULA_CAPTION,
        ComponentType.OTHER,
    }
)


def requires_native_text_extraction(
    component: DocumentComponent,
) -> bool:
    return component.component_type in NATIVE_TEXT_TYPES
