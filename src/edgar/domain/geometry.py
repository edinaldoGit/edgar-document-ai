from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BoundingBox:
    x1: int
    y1: int
    x2: int
    y2: int

    def __post_init__(self) -> None:
        if self.x1 < 0 or self.y1 < 0:
            raise ValueError("Bounding box coordinates cannot be negative.")

        if self.x2 <= self.x1:
            raise ValueError("x2 must be greater than x1.")

        if self.y2 <= self.y1:
            raise ValueError("y2 must be greater than y1.")

    @property
    def width(self) -> int:
        return self.x2 - self.x1

    @property
    def height(self) -> int:
        return self.y2 - self.y1

    @property
    def area(self) -> int:
        return self.width * self.height

    @property
    def centroid(self) -> tuple[float, float]:
        return (
            (self.x1 + self.x2) / 2,
            (self.y1 + self.y2) / 2,
        )
