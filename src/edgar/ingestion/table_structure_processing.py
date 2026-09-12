from edgar.domain import (
    ComponentType,
    Document,
    DocumentComponent,
    DocumentPage,
)
from edgar.ingestion.contracts import TableStructureExtractor


class TableStructureProcessor:
    def __init__(self, *, extractor: TableStructureExtractor):
        self._extractor = extractor

    def process(
        self,
        document: Document,
        page: DocumentPage,
        components: list[DocumentComponent],
    ) -> list[DocumentComponent]:
        for component in components:
            if component.component_type != ComponentType.TABLE:
                continue

            component.table_structure = self._extractor.extract(
                document,
                page,
                component,
            )

        return components
