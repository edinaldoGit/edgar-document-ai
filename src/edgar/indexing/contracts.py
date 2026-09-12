from typing import Protocol

from edgar.indexing.embedded_records import EmbeddedIndexRecord


class TextEmbedder(Protocol):
    def embed(
        self,
        texts: list[str],
    ) -> list[list[float]]: ...


class EmbeddedRecordStore(Protocol):
    def upsert(
        self,
        records: list[EmbeddedIndexRecord],
    ) -> None: ...
