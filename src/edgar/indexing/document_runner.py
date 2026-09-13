from edgar.domain import Document
from edgar.indexing.embedded_records import EmbeddedIndexRecord
from edgar.indexing.pipeline import IndexingPipeline
from edgar.ingestion.document_runner import DocumentIngestionRunner


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
    ) -> list[EmbeddedIndexRecord]:
        components = self._ingestion_runner.run(document)

        return self._indexing_pipeline.index(components)
