from edgar.domain import Document, DocumentComponent, DocumentPage
from edgar.ingestion.contracts import TextExtractor
from edgar.ingestion.text_extraction_policy import (
    requires_native_text_extraction,
)


class NativeTextProcessor:
    def __init__(self, *, extractor: TextExtractor):
        self._extractor = extractor

    def process(
        self,
        document: Document,
        page: DocumentPage,
        components: list[DocumentComponent],
    ) -> list[DocumentComponent]:
        for component in components:
            if not requires_native_text_extraction(component):
                continue

            component.text_extracted = self._extractor.extract(
                document,
                page,
                component,
            )

        return components
