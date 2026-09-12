from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PositionedWord:
    text: str
    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def y_center(self) -> float:
        return (self.y0 + self.y1) / 2


def group_words_into_rows(
    words: list[PositionedWord],
    *,
    y_tolerance: float = 2.0,
) -> list[list[PositionedWord]]:
    if y_tolerance < 0:
        raise ValueError("Y tolerance must not be negative.")

    rows: list[list[PositionedWord]] = []

    for word in sorted(
        words,
        key=lambda item: (item.y_center, item.x0),
    ):
        matching_row = None

        for row in rows:
            row_y = sum(item.y_center for item in row) / len(row)

            if abs(word.y_center - row_y) <= y_tolerance:
                matching_row = row
                break

        if matching_row is None:
            rows.append([word])
        else:
            matching_row.append(word)

    for row in rows:
        row.sort(key=lambda item: item.x0)

    return rows


@dataclass(frozen=True, slots=True)
class PositionedText:
    text: str
    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def x_center(self) -> float:
        return (self.x0 + self.x1) / 2

    @property
    def y_center(self) -> float:
        return (self.y0 + self.y1) / 2


def nearest_column_index(
    item: PositionedText,
    header_cells: list[PositionedText],
) -> int:
    if not header_cells:
        raise ValueError("Header cells must not be empty.")

    return min(
        range(len(header_cells)),
        key=lambda index: abs(item.x_center - header_cells[index].x_center),
    )


def merge_continuation_rows(
    rows: list[list[str | None]],
) -> list[list[str | None]]:
    logical_rows: list[list[str | None]] = []

    for row in rows:
        if not row:
            continue

        has_non_first_column_content = any(value for value in row[1:])

        if has_non_first_column_content or not logical_rows:
            logical_rows.append(row.copy())
            continue

        continuation = row[0]

        if not continuation:
            continue

        previous = logical_rows[-1]

        if previous[0]:
            previous[0] = f"{previous[0]} {continuation}"
        else:
            previous[0] = continuation

    return logical_rows


def place_items_in_columns(
    items: list[PositionedText],
    header_cells: list[PositionedText],
) -> list[str | None]:
    if not header_cells:
        raise ValueError("Header cells must not be empty.")

    row: list[str | None] = [None] * len(header_cells)

    for item in sorted(items, key=lambda value: value.x0):
        column_index = nearest_column_index(
            item,
            header_cells,
        )

        if row[column_index] is None:
            row[column_index] = item.text
        else:
            row[column_index] = f"{row[column_index]} {item.text}"

    return row


def reconstruct_table(
    items: list[PositionedText],
    *,
    y_tolerance: float = 1.0,
) -> tuple[list[str], list[list[str | None]]]:
    if y_tolerance < 0:
        raise ValueError("Y tolerance must not be negative.")

    if not items:
        return [], []

    visual_groups: list[list[PositionedText]] = []

    for item in sorted(
        items,
        key=lambda value: (
            value.y_center,
            value.x0,
        ),
    ):
        matching_group = None

        for group in visual_groups:
            group_y = sum(value.y_center for value in group) / len(group)

            if abs(item.y_center - group_y) <= y_tolerance:
                matching_group = group
                break

        if matching_group is None:
            visual_groups.append([item])
        else:
            matching_group.append(item)

    header_cells = sorted(
        visual_groups[0],
        key=lambda value: value.x0,
    )

    header = [item.text for item in header_cells]

    visual_rows = [
        place_items_in_columns(
            group,
            header_cells,
        )
        for group in visual_groups[1:]
    ]

    logical_rows = merge_continuation_rows(
        visual_rows,
    )

    return header, logical_rows
