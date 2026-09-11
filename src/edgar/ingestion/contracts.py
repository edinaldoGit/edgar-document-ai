from collections.abc import Sequence
from typing import Protocol

from edgar.domain import Document, DocumentComponent, DocumentPage


class PageRasterizer(Protocol):
    def rasterize(self, document: Document) -> list[DocumentPage]: ...


class LayoutAnalyzer(Protocol):
    def analyze(self, page: DocumentPage) -> list[DocumentComponent]: ...


class GeometryProcessor(Protocol):
    def process(
        self,
        page: DocumentPage,
        components: Sequence[DocumentComponent],
    ) -> list[DocumentComponent]: ...


class TextExtractor(Protocol):
    def extract(
        self,
        document: Document,
        page: DocumentPage,
        component: DocumentComponent,
    ) -> str | None: ...


class VisualDescriber(Protocol):
    def describe(self, component: DocumentComponent) -> str | None: ...


class ComponentIndexer(Protocol):
    def index(self, components: Sequence[DocumentComponent]) -> None: ...
