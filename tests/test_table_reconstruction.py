import pytest

from edgar.ingestion.table_structure import (
    PositionedText,
    reconstruct_table,
)


def item(text, x0, y, x1):
    return PositionedText(
        text=text,
        x0=x0,
        y0=y - 1,
        x1=x1,
        y1=y + 1,
    )


def test_reconstructs_multiline_schedule_rows():
    items = [
        item("Atividades", 87.3, 270.6, 128.1),
        item("Mar", 219.3, 270.6, 236.2),
        item("Abr", 252.7, 270.6, 268.2),
        item("Mai", 285.4, 270.6, 300.9),
        item(
            "Definição do tema e delimitação",
            87.3,
            281.1,
            203.4,
        ),
        item("X", 224.5, 281.1, 231.0),
        item(
            "do problema",
            87.3,
            291.0,
            132.4,
        ),
        item(
            "Revisão bibliográfica e trabalhos",
            87.3,
            301.4,
            204.9,
        ),
        item("X", 224.5, 301.4, 231.0),
        item("X", 257.2, 301.4, 263.7),
        item(
            "relacionados",
            87.3,
            311.4,
            132.7,
        ),
    ]

    header, rows = reconstruct_table(items)

    assert header == [
        "Atividades",
        "Mar",
        "Abr",
        "Mai",
    ]

    assert rows == [
        [
            "Definição do tema e delimitação do problema",
            "X",
            None,
            None,
        ],
        [
            "Revisão bibliográfica e trabalhos relacionados",
            "X",
            "X",
            None,
        ],
    ]


def test_reconstruct_table_returns_empty_result_for_no_items():
    assert reconstruct_table([]) == ([], [])


def test_reconstruct_table_rejects_negative_y_tolerance():
    with pytest.raises(ValueError):
        reconstruct_table(
            [],
            y_tolerance=-1,
        )
