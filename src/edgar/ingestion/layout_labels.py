from edgar.domain import ComponentType

_LAYOUT_LABELS: dict[str, ComponentType] = {
    "title": ComponentType.TITLE,
    "plain text": ComponentType.PLAIN_TEXT,
    "plain_text": ComponentType.PLAIN_TEXT,
    "abandon": ComponentType.ABANDON,
    "figure": ComponentType.FIGURE,
    "figure_caption": ComponentType.FIGURE_CAPTION,
    "table": ComponentType.TABLE,
    "table_caption": ComponentType.TABLE_CAPTION,
    "table_footnote": ComponentType.TABLE_FOOTNOTE,
    "isolate_formula": ComponentType.ISOLATE_FORMULA,
    "formula_caption": ComponentType.FORMULA_CAPTION,
}


def map_layout_label(label: str) -> ComponentType:
    normalized = label.strip().lower()
    return _LAYOUT_LABELS.get(normalized, ComponentType.OTHER)
