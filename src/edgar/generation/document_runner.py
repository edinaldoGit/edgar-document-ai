from edgar.domain import Document
from edgar.generation.pipeline import AnsweringPipeline
from edgar.generation.results import AnswerResult
from edgar.indexing.document_runner import DocumentIndexingRunner


class DocumentAnsweringRunner:
    def __init__(
        self,
        *,
        indexing_runner: DocumentIndexingRunner,
        answering_pipeline: AnsweringPipeline,
    ):
        self._indexing_runner = indexing_runner
        self._answering_pipeline = answering_pipeline

    def run(
        self,
        document: Document,
        question: str,
        *,
        limit: int = 5,
    ) -> AnswerResult:
        self._indexing_runner.run(document)

        return self._answering_pipeline.answer(
            question,
            limit=limit,
            doc_id=document.doc_id,
        )
