from collections.abc import Sequence

from edgar.domain import DocumentComponent, DocumentPage
from edgar.ingestion.caption_association import (
    associate_figure_captions,
    associate_formula_captions,
    associate_table_captions,
)
from edgar.ingestion.table_association import (
    associate_table_footnotes,
)


class ComponentAssociationProcessor:
    def process(
        self,
        page: DocumentPage,
        components: Sequence[DocumentComponent],
    ) -> list[DocumentComponent]:
        processed = list(components)

        associate_figure_captions(processed)
        associate_formula_captions(processed)
        associate_table_captions(processed)
        associate_table_footnotes(processed)

        return processed
