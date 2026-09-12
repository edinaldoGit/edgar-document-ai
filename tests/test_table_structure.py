import pytest

from edgar.ingestion.table_structure import (
    PositionedText,
    PositionedWord,
    group_words_into_rows,
    merge_continuation_rows,
    nearest_column_index,
    place_items_in_columns,
)


def word(text, x0, y_center):
    return PositionedWord(
        text=text,
        x0=x0,
        y0=y_center - 1,
        x1=x0 + 10,
        y1=y_center + 1,
    )


def test_groups_words_from_same_visual_row():
    words = [
        word("Critério", 89.4, 137.7),
        word("ColPali", 238.4, 137.7),
        word("LILaC", 311.9, 137.8),
        word("SLEUTH", 387.1, 137.6),
        word("EDGAR", 474.0, 137.7),
    ]

    rows = group_words_into_rows(words)

    assert len(rows) == 1

    assert [item.text for item in rows[0]] == [
        "Critério",
        "ColPali",
        "LILaC",
        "SLEUTH",
        "EDGAR",
    ]


def test_separates_distinct_table_rows():
    words = [
        word("Critério", 89.4, 137.7),
        word("ColPali", 238.4, 137.7),
        word("Granularidade", 89.4, 152.9),
        word("Página", 227.9, 152.9),
        word("Custo", 89.4, 163.5),
        word("Baixo", 241.7, 163.5),
    ]

    rows = group_words_into_rows(words)

    assert len(rows) == 3

    assert [item.text for item in rows[0]] == [
        "Critério",
        "ColPali",
    ]

    assert [item.text for item in rows[1]] == [
        "Granularidade",
        "Página",
    ]

    assert [item.text for item in rows[2]] == [
        "Custo",
        "Baixo",
    ]


def test_sorts_words_left_to_right_inside_row():
    words = [
        word("EDGAR", 474.0, 137.7),
        word("Critério", 89.4, 137.7),
        word("LILaC", 311.9, 137.7),
    ]

    rows = group_words_into_rows(words)

    assert [item.text for item in rows[0]] == [
        "Critério",
        "LILaC",
        "EDGAR",
    ]


def test_rejects_negative_y_tolerance():
    with pytest.raises(ValueError):
        group_words_into_rows(
            [],
            y_tolerance=-1,
        )


def test_assigns_table_cell_to_nearest_header_column():
    header = [
        PositionedText("Critério", 89.4, 0, 119.7, 10),
        PositionedText("ColPali", 238.4, 0, 266.2, 10),
        PositionedText("LILaC", 311.9, 0, 337.8, 10),
        PositionedText("SLEUTH", 387.1, 0, 422.9, 10),
        PositionedText("EDGAR", 474.0, 0, 505.8, 10),
    ]

    criterion = PositionedText(
        "Preserva relações entre componentes",
        89.4,
        20,
        219.1,
        30,
    )

    edgar_value = PositionedText(
        "Sim",
        482.8,
        20,
        497.0,
        30,
    )

    assert nearest_column_index(criterion, header) == 0
    assert nearest_column_index(edgar_value, header) == 4


def test_assigns_wide_cell_by_its_horizontal_center():
    header = [
        PositionedText("Critério", 89.4, 0, 119.7, 10),
        PositionedText("ColPali", 238.4, 0, 266.2, 10),
        PositionedText("LILaC", 311.9, 0, 337.8, 10),
        PositionedText("SLEUTH", 387.1, 0, 422.9, 10),
        PositionedText("EDGAR", 474.0, 0, 505.8, 10),
    ]

    value = PositionedText(
        "Moderado (Estimativa)",
        449.1,
        20,
        530.7,
        30,
    )

    assert nearest_column_index(value, header) == 4


def test_nearest_column_rejects_empty_header():
    item = PositionedText(
        "texto",
        10,
        10,
        20,
        20,
    )

    with pytest.raises(ValueError):
        nearest_column_index(item, [])


def test_merges_first_column_continuation_into_previous_logical_row():
    rows = [
        [
            "Definição do tema e delimitação",
            "X",
            None,
        ],
        [
            "do problema",
            None,
            None,
        ],
    ]

    result = merge_continuation_rows(rows)

    assert result == [
        [
            "Definição do tema e delimitação do problema",
            "X",
            None,
        ]
    ]


def test_merges_multiple_continuation_lines():
    rows = [
        [
            "Definição dos componentes",
            None,
            None,
            "X",
            "X",
        ],
        [
            "tecnológicos e do plano de",
            None,
            None,
            None,
            None,
        ],
        [
            "avaliação",
            None,
            None,
            None,
            None,
        ],
    ]

    result = merge_continuation_rows(rows)

    assert result == [
        [
            "Definição dos componentes tecnológicos e do plano de avaliação",
            None,
            None,
            "X",
            "X",
        ]
    ]


def test_row_with_non_first_column_content_starts_new_logical_row():
    rows = [
        [
            "Primeira atividade",
            "X",
            None,
        ],
        [
            "Segunda atividade",
            None,
            "X",
        ],
    ]

    result = merge_continuation_rows(rows)

    assert result == rows


def test_places_visual_row_items_in_header_columns():
    header = [
        PositionedText("Atividades", 87.3, 0, 128.1, 10),
        PositionedText("Mar", 219.3, 0, 236.2, 10),
        PositionedText("Abr", 252.7, 0, 268.2, 10),
        PositionedText("Mai", 285.4, 0, 300.9, 10),
    ]

    items = [
        PositionedText(
            "Revisão bibliográfica e trabalhos",
            87.3,
            20,
            204.9,
            30,
        ),
        PositionedText(
            "X",
            224.5,
            20,
            231.0,
            30,
        ),
        PositionedText(
            "X",
            257.2,
            20,
            263.7,
            30,
        ),
    ]

    result = place_items_in_columns(
        items,
        header,
    )

    assert result == [
        "Revisão bibliográfica e trabalhos",
        "X",
        "X",
        None,
    ]


def test_combines_multiple_items_assigned_to_same_column():
    header = [
        PositionedText("Critério", 89.4, 0, 119.7, 10),
        PositionedText("EDGAR", 474.0, 0, 505.8, 10),
    ]

    items = [
        PositionedText(
            "Moderado",
            449.1,
            20,
            487.0,
            30,
        ),
        PositionedText(
            "(Estimativa)",
            487.5,
            20,
            530.7,
            30,
        ),
    ]

    result = place_items_in_columns(
        items,
        header,
    )

    assert result == [
        None,
        "Moderado (Estimativa)",
    ]


def test_place_items_rejects_empty_header():
    item = PositionedText(
        "texto",
        10,
        10,
        20,
        20,
    )

    with pytest.raises(ValueError):
        place_items_in_columns(
            [item],
            [],
        )
