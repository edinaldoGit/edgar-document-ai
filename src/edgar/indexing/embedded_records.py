from dataclasses import dataclass

from edgar.indexing.records import IndexRecord


@dataclass(frozen=True, slots=True)
class EmbeddedIndexRecord:
    record: IndexRecord
    embedding: tuple[float, ...]

    def __post_init__(self) -> None:
        if not self.embedding:
            raise ValueError("Embedding cannot be empty.")

    @property
    def dimension(self) -> int:
        return len(self.embedding)
