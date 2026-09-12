from dataclasses import dataclass
from uuid import UUID

from edgar.domain import BoundingBox, ComponentType


@dataclass(frozen=True, slots=True)
class RetrievedEvidence:
    component_id: UUID
    doc_id: UUID
    page_index: int
    component_type: ComponentType
    bbox: BoundingBox
    text: str
    score: float

    text_extracted: str | None = None
    visual_description: str | None = None
    crop_ref: str | None = None

    @property
    def page_number(self) -> int:
        return self.page_index + 1
