from collections.abc import Sequence

from edgar.domain import DocumentComponent, DocumentPage


class IdentityGeometryProcessor:
    def process(
        self,
        page: DocumentPage,
        components: Sequence[DocumentComponent],
    ) -> list[DocumentComponent]:
        return list(components)
