import pytest

from edgar.domain import ComponentType
from edgar.ingestion.visual_description_prompts import (
    visual_description_prompt,
)


def test_figure_prompt_is_specific_to_figures():
    prompt = visual_description_prompt(ComponentType.FIGURE)

    assert "figure" in prompt.lower()
    assert "labels" in prompt.lower()
    assert "relationships" in prompt.lower()
    assert "portuguese" in prompt.lower()


def test_table_prompt_preserves_table_structure():
    prompt = visual_description_prompt(ComponentType.TABLE)

    assert "table" in prompt.lower()
    assert "rows and columns" in prompt.lower()
    assert "cell values" in prompt.lower()
    assert "unordered sequence" in prompt.lower()


@pytest.mark.parametrize(
    "component_type",
    [
        ComponentType.PLAIN_TEXT,
        ComponentType.TITLE,
        ComponentType.ISOLATE_FORMULA,
        ComponentType.FIGURE_CAPTION,
        ComponentType.TABLE_CAPTION,
        ComponentType.TABLE_FOOTNOTE,
        ComponentType.FORMULA_CAPTION,
        ComponentType.ABANDON,
        ComponentType.OTHER,
    ],
)
def test_unsupported_component_type_is_rejected(component_type):
    with pytest.raises(ValueError):
        visual_description_prompt(component_type)
