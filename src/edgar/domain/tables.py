from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TableStructure:
    header: tuple[str, ...]
    rows: tuple[tuple[str | None, ...], ...]

    def __post_init__(self) -> None:
        if not self.header:
            raise ValueError("Table header cannot be empty.")

        column_count = len(self.header)

        for row in self.rows:
            if len(row) != column_count:
                raise ValueError(
                    "Every table row must have the same number of columns as the header."
                )

    @property
    def column_count(self) -> int:
        return len(self.header)

    @property
    def row_count(self) -> int:
        return len(self.rows)
