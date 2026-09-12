from edgar.domain import Document, DocumentComponent, DocumentPage
from edgar.ingestion.contracts import TextExtractor


class FallbackTextExtractor:
    def __init__(
        self,
        *,
        primary: TextExtractor,
        fallback: TextExtractor,
    ):
        self._primary = primary
        self._fallback = fallback

    def extract(
        self,
        document: Document,
        page: DocumentPage,
        component: DocumentComponent,
    ) -> str | None:
        text = self._primary.extract(
            document,
            page,
            component,
        )

        if text is not None:
            return text

        return self._fallback.extract(
            document,
            page,
            component,
        )
