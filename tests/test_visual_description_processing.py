from uuid import uuid4

from edgar.domain import BoundingBox, ComponentType, DocumentComponent
from edgar.ingestion.visual_description_processing import (
    VisualDescriptionProcessor,
)


class RecordingVisualDescriber:
    def __init__(self):
        self.calls = []

    def describe(
        self,
        component,
        *,
        prompt,
        context=None,
    ):
        self.calls.append(
            {
                "component": component,
                "prompt": prompt,
                "context": context,
            }
        )

        return f"description:{component.component_type.value}"


def make_component(
    doc_id,
    component_type,
    *,
    parent_component_id=None,
    text_extracted=None,
):
    return DocumentComponent(
        doc_id=doc_id,
        page_index=0,
        component_type=component_type,
        bbox=BoundingBox(
            x1=10,
            y1=10,
            x2=100,
            y2=50,
        ),
        parent_component_id=parent_component_id,
        text_extracted=text_extracted,
    )


def test_process_describes_figure_with_caption_context():
    doc_id = uuid4()

    figure = make_component(
        doc_id,
        ComponentType.FIGURE,
    )

    caption = make_component(
        doc_id,
        ComponentType.FIGURE_CAPTION,
        parent_component_id=figure.component_id,
        text_extracted="Arquitetura proposta do sistema.",
    )

    describer = RecordingVisualDescriber()
    processor = VisualDescriptionProcessor(
        describer=describer,
    )

    components = [figure, caption]

    result = processor.process(components)

    assert result is components
    assert len(describer.calls) == 1

    call = describer.calls[0]

    assert call["component"] is figure
    assert "figure" in call["prompt"].lower()
    assert call["context"] == ("Figure caption: Arquitetura proposta do sistema.")

    assert figure.visual_description == "description:figure"
    assert caption.visual_description is None


def test_process_describes_table_with_caption_and_footnote():
    doc_id = uuid4()

    table = make_component(
        doc_id,
        ComponentType.TABLE,
    )

    caption = make_component(
        doc_id,
        ComponentType.TABLE_CAPTION,
        parent_component_id=table.component_id,
        text_extracted="Tabela 1 – Trabalhos relacionados.",
    )

    footnote = make_component(
        doc_id,
        ComponentType.TABLE_FOOTNOTE,
        parent_component_id=table.component_id,
        text_extracted="Fonte: Elaborado pelo autor.",
    )

    describer = RecordingVisualDescriber()
    processor = VisualDescriptionProcessor(
        describer=describer,
    )

    processor.process(
        [footnote, table, caption],
    )

    assert len(describer.calls) == 1

    call = describer.calls[0]

    assert call["component"] is table
    assert "table" in call["prompt"].lower()
    assert call["context"] == (
        "Table caption: Tabela 1 – Trabalhos relacionados.\n"
        "Table footnote: Fonte: Elaborado pelo autor."
    )

    assert table.visual_description == "description:table"


def test_process_skips_non_visual_components():
    doc_id = uuid4()

    text = make_component(
        doc_id,
        ComponentType.PLAIN_TEXT,
    )

    formula = make_component(
        doc_id,
        ComponentType.ISOLATE_FORMULA,
    )

    describer = RecordingVisualDescriber()
    processor = VisualDescriptionProcessor(
        describer=describer,
    )

    processor.process(
        [text, formula],
    )

    assert describer.calls == []
    assert text.visual_description is None
    assert formula.visual_description is None


def test_process_preserves_none_when_description_is_unavailable():
    class EmptyVisualDescriber:
        def describe(
            self,
            component,
            *,
            prompt,
            context=None,
        ):
            return None

    doc_id = uuid4()

    figure = make_component(
        doc_id,
        ComponentType.FIGURE,
    )

    processor = VisualDescriptionProcessor(
        describer=EmptyVisualDescriber(),
    )

    processor.process([figure])

    assert figure.visual_description is None
