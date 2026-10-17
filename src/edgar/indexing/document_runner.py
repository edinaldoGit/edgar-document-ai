from edgar.domain import Document
from edgar.indexing.embedded_records import EmbeddedIndexRecord
from edgar.indexing.pipeline import IndexingPipeline
from edgar.ingestion.document_runner import DocumentIngestionRunner, ProgressCallback


class DocumentIndexingRunner:
    def __init__(
        self,
        *,
        ingestion_runner: DocumentIngestionRunner,
        indexing_pipeline: IndexingPipeline,
    ):
        self._ingestion_runner = ingestion_runner
        self._indexing_pipeline = indexing_pipeline

    def run(
        self,
        document: Document,
        *,
        progress_callback: ProgressCallback | None = None,
    ) -> list[EmbeddedIndexRecord]:
        if progress_callback is None:
            components = self._ingestion_runner.run(document)
        else:
            components = self._ingestion_runner.run(
                document,
                progress_callback=progress_callback,
            )
            progress_callback("indexing", 0, 1)

        records = self._indexing_pipeline.index(components)

        if progress_callback is not None:
            progress_callback("indexing", 1, 1)

        return records
