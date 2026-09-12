from dataclasses import dataclass
from uuid import UUID

from edgar.domain import BoundingBox, ComponentType


@dataclass(frozen=True, slots=True)
class IndexRecord:
    component_id: UUID
    doc_id: UUID
    page_index: int
    component_type: ComponentType
    bbox: BoundingBox
    text: str

    text_extracted: str | None = None
    visual_description: str | None = None
    crop_ref: str | None = None

    def __post_init__(self) -> None:
        if self.page_index < 0:
            raise ValueError("Page index cannot be negative.")

        if not self.text.strip():
            raise ValueError("Indexable text cannot be blank.")

    @property
    def page_number(self) -> int:
        return self.page_index + 1
