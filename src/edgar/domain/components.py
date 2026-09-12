from dataclasses import dataclass, field
from enum import Enum
from uuid import UUID, uuid4

from edgar.domain.geometry import BoundingBox
from edgar.domain.tables import TableStructure


class ComponentType(str, Enum):
    PLAIN_TEXT = "plain_text"
    TITLE = "title"
    TABLE = "table"
    FIGURE = "figure"
    ISOLATE_FORMULA = "isolate_formula"
    FIGURE_CAPTION = "figure_caption"
    TABLE_CAPTION = "table_caption"
    TABLE_FOOTNOTE = "table_footnote"
    FORMULA_CAPTION = "formula_caption"
    ABANDON = "abandon"
    OTHER = "other"


@dataclass(slots=True, kw_only=True)
class DocumentComponent:
    doc_id: UUID
    page_index: int
    component_type: ComponentType
    bbox: BoundingBox

    detection_confidence: float | None = None
    text_extracted: str | None = None
    visual_description: str | None = None
    table_structure: TableStructure | None = None
    crop_ref: str | None = None
    parent_component_id: UUID | None = None

    component_id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if self.page_index < 0:
            raise ValueError("Page index cannot be negative.")

        if self.detection_confidence is not None:
            if not 0 <= self.detection_confidence <= 1:
                raise ValueError("Detection confidence must be between 0 and 1.")

        if self.parent_component_id == self.component_id:
            raise ValueError("A component cannot be its own parent.")

    @property
    def page_number(self) -> int:
        return self.page_index + 1
