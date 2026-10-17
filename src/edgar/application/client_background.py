from pathlib import Path
from threading import Lock

from edgar.application.client_session import ClientDocumentSession
from edgar.domain import Document
from edgar.generation.results import AnswerResult


class IngestionProgress:
    def __init__(self) -> None:
        self._lock = Lock()
        self._stage = "waiting"
        self._completed = 0
        self._total = 0

    def update(
        self,
        stage: str,
        completed: int,
        total: int,
    ) -> None:
        with self._lock:
            self._stage = stage
            self._completed = completed
            self._total = total

    def snapshot(self) -> tuple[str, int, int]:
        with self._lock:
            return (
                self._stage,
                self._completed,
                self._total,
            )


def process_client_document(
    *,
    document: Document,
    storage_root: str | Path,
    progress: IngestionProgress | None = None,
) -> int:
    root = Path(storage_root)

    session = ClientDocumentSession(
        storage_root=root,
        qdrant_path=root / "qdrant",
    )

    try:
        if progress is None:
            indexed_count = session.ingest(document)
        else:
            indexed_count = session.ingest(
                document,
                progress_callback=progress.update,
            )

        if indexed_count <= 0:
            raise RuntimeError("O processamento não produziu registros indexáveis.")

        return indexed_count

    finally:
        session.close()


def answer_client_question(
    *,
    question: str,
    document: Document,
    storage_root: str | Path,
    limit: int = 8,
) -> AnswerResult:
    root = Path(storage_root)

    session = ClientDocumentSession(
        storage_root=root,
        qdrant_path=root / "qdrant",
    )

    try:
        return session.answer(
            question,
            doc_id=document.doc_id,
            limit=limit,
        )
    finally:
        session.close()
