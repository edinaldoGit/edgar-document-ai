from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True, kw_only=True)
class Document:
    filename: str
    source_ref: str
    page_count: int

    doc_id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if not self.filename.strip():
            raise ValueError("Filename cannot be empty.")

        if not self.source_ref.strip():
            raise ValueError("Source reference cannot be empty.")

        if self.page_count <= 0:
            raise ValueError("Page count must be greater than zero.")
