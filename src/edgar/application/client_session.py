from pathlib import Path
from uuid import UUID

from qdrant_client import QdrantClient

from edgar.application.bootstrap import build_ingestion_runner
from edgar.domain import Document
from edgar.generation.pipeline import AnsweringPipeline
from edgar.indexing.document_runner import DocumentIndexingRunner
from edgar.indexing.pipeline import IndexingPipeline
from edgar.infrastructure.modal_answer_generation_client import ModalAnswerGenerationClient
from edgar.infrastructure.modal_answer_generator import ModalAnswerGenerator
from edgar.infrastructure.modal_embedding_client import ModalEmbeddingClient
from edgar.infrastructure.modal_text_embedder import ModalTextEmbedder
from edgar.infrastructure.qdrant_vector_store import QdrantVectorStore
from edgar.ingestion.document_runner import ProgressCallback
from edgar.retrieval.semantic import SemanticRetriever


class ClientDocumentSession:
    def __init__(
        self,
        *,
        storage_root: str | Path,
        qdrant_path: str | Path,
    ) -> None:
        storage_root = Path(storage_root)
        qdrant_path = Path(qdrant_path)
        qdrant_path.mkdir(parents=True, exist_ok=True)

        self._client = QdrantClient(path=str(qdrant_path))

        store = QdrantVectorStore(client=self._client)
        embedder = ModalTextEmbedder(client=ModalEmbeddingClient())

        self._indexer = DocumentIndexingRunner(
            ingestion_runner=build_ingestion_runner(
                storage_root=storage_root,
            ),
            indexing_pipeline=IndexingPipeline(
                embedder=embedder,
                store=store,
            ),
        )

        self._answering = AnsweringPipeline(
            retriever=SemanticRetriever(
                embedder=embedder,
                searcher=store,
            ),
            generator=ModalAnswerGenerator(
                client=ModalAnswerGenerationClient(),
                max_new_tokens=256,
            ),
        )

    def ingest(
        self,
        document: Document,
        *,
        progress_callback: ProgressCallback | None = None,
    ) -> int:
        if progress_callback is None:
            records = self._indexer.run(document)
        else:
            records = self._indexer.run(
                document,
                progress_callback=progress_callback,
            )

        return len(records)

    def answer(
        self,
        question: str,
        *,
        doc_id: UUID,
        limit: int = 10,
    ):
        return self._answering.answer(
            question,
            doc_id=doc_id,
            limit=limit,
        )

    def close(self) -> None:
        self._client.close()
