from edgar.domain import DocumentComponent
from edgar.indexing.contracts import (
    EmbeddedRecordStore,
    TextEmbedder,
)
from edgar.indexing.embedded_records import EmbeddedIndexRecord
from edgar.indexing.embedding import embed_index_records
from edgar.indexing.preparation import prepare_index_records


class IndexingPipeline:
    def __init__(
        self,
        *,
        embedder: TextEmbedder,
        store: EmbeddedRecordStore,
    ):
        self._embedder = embedder
        self._store = store

    def index(
        self,
        components: list[DocumentComponent],
    ) -> list[EmbeddedIndexRecord]:
        records = prepare_index_records(
            components,
        )

        embedded_records = embed_index_records(
            records,
            embedder=self._embedder,
        )

        self._store.upsert(
            embedded_records,
        )

        return embedded_records
