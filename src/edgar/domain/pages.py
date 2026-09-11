from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True, kw_only=True)
class DocumentPage:
    doc_id: UUID
    page_index: int
    width: int
    height: int
    render_dpi: int
    image_ref: str

    def __post_init__(self) -> None:
        if self.page_index < 0:
            raise ValueError("Page index cannot be negative.")

        if self.width <= 0:
            raise ValueError("Page width must be greater than zero.")

        if self.height <= 0:
            raise ValueError("Page height must be greater than zero.")

        if self.render_dpi <= 0:
            raise ValueError("Render DPI must be greater than zero.")

        if not self.image_ref.strip():
            raise ValueError("Image reference cannot be empty.")

    @property
    def page_number(self) -> int:
        return self.page_index + 1

    @property
    def dimensions(self) -> tuple[int, int]:
        return self.width, self.height
