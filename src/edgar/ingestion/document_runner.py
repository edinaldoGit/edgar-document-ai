from edgar.domain import Document, DocumentComponent
from edgar.ingestion.contracts import PageRasterizer
from edgar.ingestion.pipeline import IngestionPipeline


class DocumentIngestionRunner:
    def __init__(
        self,
        *,
        rasterizer: PageRasterizer,
        pipeline: IngestionPipeline,
    ):
        self._rasterizer = rasterizer
        self._pipeline = pipeline

    def run(
        self,
        document: Document,
    ) -> list[DocumentComponent]:
        pages = self._rasterizer.rasterize(document)

        components: list[DocumentComponent] = []

        for page in pages:
            page_components = self._pipeline.process_page(
                document,
                page,
            )

            components.extend(page_components)

        return components
