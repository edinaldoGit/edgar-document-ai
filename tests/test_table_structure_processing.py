from uuid import uuid4

from edgar.domain import (
    BoundingBox,
    ComponentType,
    Document,
    DocumentComponent,
    DocumentPage,
    TableStructure,
)
from edgar.ingestion.table_structure_processing import (
    TableStructureProcessor,
)


class FakeTableStructureExtractor:
    def __init__(self):
        self.calls = []

    def extract(
        self,
        document,
        page,
        component,
    ):
        self.calls.append(
            (
                document,
                page,
                component,
            )
        )

        return TableStructure(
            header=(
                "Critério",
                "EDGAR",
            ),
            rows=(
                (
                    "Suporte visual",
                    "Sim",
                ),
            ),
        )


def test_populates_table_structure_only_for_tables():
    doc_id = uuid4()

    document = Document(
        filename="document.pdf",
        source_ref="document.pdf",
        page_count=1,
        doc_id=doc_id,
    )

    page = DocumentPage(
        doc_id=doc_id,
        page_index=0,
        width=1000,
        height=1400,
        render_dpi=300,
        image_ref="page.png",
    )

    table = DocumentComponent(
        doc_id=doc_id,
        page_index=0,
        component_type=ComponentType.TABLE,
        bbox=BoundingBox(
            x1=10,
            y1=20,
            x2=500,
            y2=400,
        ),
    )

    figure = DocumentComponent(
        doc_id=doc_id,
        page_index=0,
        component_type=ComponentType.FIGURE,
        bbox=BoundingBox(
            x1=520,
            y1=20,
            x2=900,
            y2=400,
        ),
    )

    extractor = FakeTableStructureExtractor()

    processor = TableStructureProcessor(
        extractor=extractor,
    )

    result = processor.process(
        document,
        page,
        [
            table,
            figure,
        ],
    )

    assert result == [
        table,
        figure,
    ]

    assert table.table_structure == TableStructure(
        header=(
            "Critério",
            "EDGAR",
        ),
        rows=(
            (
                "Suporte visual",
                "Sim",
            ),
        ),
    )

    assert figure.table_structure is None

    assert extractor.calls == [
        (
            document,
            page,
            table,
        )
    ]
