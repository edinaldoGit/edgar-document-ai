import pytest

from edgar.domain import ComponentType
from edgar.ingestion.layout_labels import map_layout_label


@pytest.mark.parametrize(
    ("label", "expected"),
    [
        ("title", ComponentType.TITLE),
        ("plain text", ComponentType.PLAIN_TEXT),
        ("plain_text", ComponentType.PLAIN_TEXT),
        ("abandon", ComponentType.ABANDON),
        ("figure", ComponentType.FIGURE),
        ("figure_caption", ComponentType.FIGURE_CAPTION),
        ("table", ComponentType.TABLE),
        ("table_caption", ComponentType.TABLE_CAPTION),
        ("table_footnote", ComponentType.TABLE_FOOTNOTE),
        ("isolate_formula", ComponentType.ISOLATE_FORMULA),
        ("formula_caption", ComponentType.FORMULA_CAPTION),
    ],
)
def test_map_known_layout_label(label, expected):
    assert map_layout_label(label) == expected


def test_map_layout_label_normalizes_input():
    assert map_layout_label("  FIGURE  ") == ComponentType.FIGURE


def test_map_unknown_layout_label_to_other():
    assert map_layout_label("something_new") == ComponentType.OTHER
