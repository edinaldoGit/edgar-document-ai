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
from edgar.ingestion.text_extraction import PyMuPDFTextExtractor


def create_test_pdf(path):
    pdf = pymupdf.open()
    page = pdf.new_page(width=200, height=200)

    page.insert_text(
        (20, 50),
        "Hello EDGAR",
        fontsize=12,
    )

    pdf.save(path)
    pdf.close()


def test_extracts_native_text_from_component_region(tmp_path):
    pdf_path = tmp_path / "document.pdf"
    create_test_pdf(pdf_path)

    doc_id = uuid4()

    document = Document(
        filename="document.pdf",
        source_ref=str(pdf_path),
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
        component_type=ComponentType.PLAIN_TEXT,
        bbox=BoundingBox(
            x1=20,
            y1=50,
            x2=300,
            y2=120,
        ),
    )

    extractor = PyMuPDFTextExtractor(
        storage_root=tmp_path,
    )

    text = extractor.extract(
        document,
        page,
        component,
    )

    assert text == "Hello EDGAR"


def test_returns_none_when_component_region_has_no_native_text(tmp_path):
    pdf_path = tmp_path / "document.pdf"
    create_test_pdf(pdf_path)

    doc_id = uuid4()

    document = Document(
        filename="document.pdf",
        source_ref=str(pdf_path),
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
        component_type=ComponentType.PLAIN_TEXT,
        bbox=BoundingBox(
            x1=20,
            y1=200,
            x2=300,
            y2=260,
        ),
    )

    extractor = PyMuPDFTextExtractor(
        storage_root=tmp_path,
    )

    assert extractor.extract(document, page, component) is None


def test_rejects_component_from_different_page(tmp_path):
    pdf_path = tmp_path / "document.pdf"
    create_test_pdf(pdf_path)

    doc_id = uuid4()

    document = Document(
        filename="document.pdf",
        source_ref=str(pdf_path),
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
        page_index=1,
        component_type=ComponentType.PLAIN_TEXT,
        bbox=BoundingBox(
            x1=20,
            y1=50,
            x2=300,
            y2=120,
        ),
    )

    extractor = PyMuPDFTextExtractor(
        storage_root=tmp_path,
    )

    with pytest.raises(ValueError):
        extractor.extract(document, page, component)
