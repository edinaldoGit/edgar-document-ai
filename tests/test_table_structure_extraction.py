from types import SimpleNamespace
from uuid import uuid4

import pymupdf
import pytest

from edgar.domain import (
    BoundingBox,
    ComponentType,
    Document,
    DocumentComponent,
    DocumentPage,
)
from edgar.ingestion.table_structure_extraction import (
    PyMuPDFTableStructureExtractor,
)


class FakePDFPage:
    rect = SimpleNamespace(
        width=200.0,
        height=200.0,
    )

    def get_text(self, mode, *, clip):
        assert mode == "dict"

        return {
            "blocks": [
                {
                    "lines": [
                        {
                            "bbox": (20, 20, 80, 30),
                            "spans": [{"text": "Atividades"}],
                        },
                        {
                            "bbox": (120, 20, 140, 30),
                            "spans": [{"text": "Mar"}],
                        },
                        {
                            "bbox": (150, 20, 170, 30),
                            "spans": [{"text": "Abr"}],
                        },
                        {
                            "bbox": (20, 40, 90, 50),
                            "spans": [{"text": "Definição do"}],
                        },
                        {
                            "bbox": (125, 40, 135, 50),
                            "spans": [{"text": "X"}],
                        },
                        {
                            "bbox": (20, 55, 70, 65),
                            "spans": [{"text": "problema"}],
                        },
                        {
                            "bbox": (20, 75, 80, 85),
                            "spans": [{"text": "Revisão"}],
                        },
                        {
                            "bbox": (125, 75, 135, 85),
                            "spans": [{"text": "X"}],
                        },
                        {
                            "bbox": (155, 75, 165, 85),
                            "spans": [{"text": "X"}],
                        },
                    ]
                }
            ]
        }


class FakePDF:
    def __init__(self):
        self.page = FakePDFPage()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return None

    def __len__(self):
        return 1

    def __getitem__(self, index):
        assert index == 0
        return self.page


def make_domain_objects(source_ref):
    doc_id = uuid4()

    document = Document(
        filename="document.pdf",
        source_ref=source_ref,
        page_count=1,
        doc_id=doc_id,
    )

    page = DocumentPage(
        doc_id=doc_id,
        page_index=0,
        width=400,
        height=400,
        render_dpi=144,
        image_ref="page.png",
    )

    component = DocumentComponent(
        doc_id=doc_id,
        page_index=0,
        component_type=ComponentType.TABLE,
        bbox=BoundingBox(
            x1=0,
            y1=0,
            x2=400,
            y2=400,
        ),
    )

    return document, page, component


def test_extracts_reconstructed_table_structure(tmp_path, monkeypatch):
    pdf_path = tmp_path / "document.pdf"
    pdf_path.touch()

    document, page, component = make_domain_objects("document.pdf")

    monkeypatch.setattr(
        pymupdf,
        "open",
        lambda path: FakePDF(),
    )

    extractor = PyMuPDFTableStructureExtractor(
        storage_root=tmp_path,
    )

    table_structure = extractor.extract(
        document,
        page,
        component,
    )

    assert table_structure is not None

    assert table_structure.header == (
        "Atividades",
        "Mar",
        "Abr",
    )

    assert table_structure.rows == (
        (
            "Definição do problema",
            "X",
            None,
        ),
        (
            "Revisão",
            "X",
            "X",
        ),
    )


def test_rejects_component_from_different_page(tmp_path):
    document, page, component = make_domain_objects("document.pdf")

    component.page_index = 1

    extractor = PyMuPDFTableStructureExtractor(
        storage_root=tmp_path,
    )

    with pytest.raises(ValueError):
        extractor.extract(
            document,
            page,
            component,
        )
