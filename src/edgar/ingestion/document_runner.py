from collections.abc import Callable

from edgar.domain import Document, DocumentComponent
from edgar.ingestion.contracts import PageRasterizer
from edgar.ingestion.pipeline import IngestionPipeline

ProgressCallback = Callable[[str, int, int], None]


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
        *,
        progress_callback: ProgressCallback | None = None,
    ) -> list[DocumentComponent]:
        if progress_callback is not None:
            progress_callback("rasterizing", 0, document.page_count)

        pages = self._rasterizer.rasterize(document)

        if progress_callback is not None:
            progress_callback("processing", 0, len(pages))

        components: list[DocumentComponent] = []

        for page_number, page in enumerate(pages, start=1):
            page_components = self._pipeline.process_page(
                document,
                page,
            )
            components.extend(page_components)

            if progress_callback is not None:
                progress_callback(
                    "processing",
                    page_number,
                    len(pages),
                )

        return components
