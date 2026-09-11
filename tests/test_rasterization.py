from pathlib import Path

import pymupdf
import pytest

from edgar.domain import Document
from edgar.ingestion import PyMuPDFRasterizer


def create_test_pdf(path: Path, page_count: int = 2) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with pymupdf.open() as pdf:
        for page_number in range(1, page_count + 1):
            page = pdf.new_page(width=200, height=100)
            page.insert_text(
                (20, 50),
                f"Test page {page_number}",
            )

        pdf.save(str(path))


def test_rasterizer_uses_300_dpi_by_default(tmp_path):
    rasterizer = PyMuPDFRasterizer(storage_root=tmp_path)

    assert rasterizer.dpi == 300


def test_rasterizer_rejects_invalid_dpi(tmp_path):
    with pytest.raises(ValueError):
        PyMuPDFRasterizer(
            storage_root=tmp_path,
            dpi=0,
        )


def test_rasterize_pdf_into_document_pages(tmp_path):
    storage_root = tmp_path / "storage"

    source_ref = "documents/source/original.pdf"
    source_path = storage_root / source_ref

    create_test_pdf(source_path, page_count=2)

    document = Document(
        filename="original.pdf",
        source_ref=source_ref,
        page_count=2,
    )

    rasterizer = PyMuPDFRasterizer(
        storage_root=storage_root,
        dpi=72,
    )

    pages = rasterizer.rasterize(document)

    assert len(pages) == 2

    assert pages[0].doc_id == document.doc_id
    assert pages[0].page_index == 0
    assert pages[0].page_number == 1
    assert pages[0].render_dpi == 72
    assert pages[0].dimensions == (200, 100)

    assert pages[1].page_index == 1
    assert pages[1].page_number == 2

    for page in pages:
        image_path = storage_root / page.image_ref

        assert image_path.is_file()
        assert image_path.suffix == ".png"


def test_rasterizer_uses_sequential_page_filenames(tmp_path):
    storage_root = tmp_path / "storage"

    source_ref = "documents/source/original.pdf"
    source_path = storage_root / source_ref

    create_test_pdf(source_path, page_count=2)

    document = Document(
        filename="original.pdf",
        source_ref=source_ref,
        page_count=2,
    )

    rasterizer = PyMuPDFRasterizer(
        storage_root=storage_root,
        dpi=72,
    )

    pages = rasterizer.rasterize(document)

    assert pages[0].image_ref.endswith("page_0001.png")
    assert pages[1].image_ref.endswith("page_0002.png")


def test_rasterizer_rejects_page_count_mismatch(tmp_path):
    storage_root = tmp_path / "storage"

    source_ref = "documents/source/original.pdf"
    source_path = storage_root / source_ref

    create_test_pdf(source_path, page_count=2)

    document = Document(
        filename="original.pdf",
        source_ref=source_ref,
        page_count=3,
    )

    rasterizer = PyMuPDFRasterizer(
        storage_root=storage_root,
        dpi=72,
    )

    with pytest.raises(ValueError):
        rasterizer.rasterize(document)


def test_rasterizer_rejects_missing_pdf(tmp_path):
    document = Document(
        filename="missing.pdf",
        source_ref="documents/missing/original.pdf",
        page_count=1,
    )

    rasterizer = PyMuPDFRasterizer(storage_root=tmp_path)

    with pytest.raises(FileNotFoundError):
        rasterizer.rasterize(document)
