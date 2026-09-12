from edgar.domain import DocumentComponent
from edgar.ingestion.contracts import VisualDescriber
from edgar.ingestion.visual_context import build_visual_text_context
from edgar.ingestion.visual_description_policy import (
    requires_visual_description,
)
from edgar.ingestion.visual_description_prompts import (
    visual_description_prompt,
)


class VisualDescriptionProcessor:
    def __init__(self, *, describer: VisualDescriber):
        self._describer = describer

    def process(
        self,
        components: list[DocumentComponent],
    ) -> list[DocumentComponent]:
        for component in components:
            if not requires_visual_description(component):
                continue

            prompt = visual_description_prompt(
                component.component_type,
            )

            context = build_visual_text_context(
                component,
                components,
            )

            component.visual_description = self._describer.describe(
                component,
                prompt=prompt,
                context=context,
            )

        return components
