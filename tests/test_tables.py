import pytest

from edgar.domain.tables import TableStructure


def test_creates_table_structure():
    table = TableStructure(
        header=(
            "Critério",
            "EDGAR",
        ),
        rows=(
            (
                "Suporte visual",
                "Sim",
            ),
            (
                "Requer OCR",
                "Seletivo",
            ),
        ),
    )

    assert table.column_count == 2
    assert table.row_count == 2


def test_allows_empty_table_body():
    table = TableStructure(
        header=(
            "Critério",
            "EDGAR",
        ),
        rows=(),
    )

    assert table.row_count == 0


def test_rejects_empty_header():
    with pytest.raises(ValueError):
        TableStructure(
            header=(),
            rows=(),
        )


def test_rejects_row_with_wrong_column_count():
    with pytest.raises(ValueError):
        TableStructure(
            header=(
                "Critério",
                "EDGAR",
            ),
            rows=(("Suporte visual",),),
        )
