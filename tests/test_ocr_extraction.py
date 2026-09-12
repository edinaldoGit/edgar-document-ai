from subprocess import CompletedProcess
from uuid import uuid4

import pytest
from PIL import Image

from edgar.domain import (
    BoundingBox,
    ComponentType,
    Document,
    DocumentComponent,
    DocumentPage,
)
from edgar.ingestion.ocr_extraction import TesseractOCRTextExtractor


def make_context(tmp_path):
    doc_id = uuid4()

    image_path = tmp_path / "page.png"
    Image.new("RGB", (100, 80), "white").save(image_path)

    document = Document(
        filename="document.pdf",
        source_ref="document.pdf",
        page_count=1,
        doc_id=doc_id,
    )

    page = DocumentPage(
        doc_id=doc_id,
        page_index=0,
        width=100,
        height=80,
        render_dpi=300,
        image_ref="page.png",
    )

    component = DocumentComponent(
        doc_id=doc_id,
        page_index=0,
        component_type=ComponentType.PLAIN_TEXT,
        bbox=BoundingBox(
            x1=10,
            y1=20,
            x2=40,
            y2=50,
        ),
    )

    return document, page, component


def test_extract_returns_tesseract_text(tmp_path, monkeypatch):
    document, page, component = make_context(tmp_path)

    recorded_command = None

    def fake_run(command, **kwargs):
        nonlocal recorded_command
        recorded_command = command

        with Image.open(command[1]) as crop:
            assert crop.size == (30, 30)

        return CompletedProcess(
            args=command,
            returncode=0,
            stdout="Texto reconhecido\n",
            stderr="",
        )

    monkeypatch.setattr(
        "edgar.ingestion.ocr_extraction.subprocess.run",
        fake_run,
    )

    extractor = TesseractOCRTextExtractor(
        storage_root=tmp_path,
    )

    text = extractor.extract(
        document,
        page,
        component,
    )

    assert text == "Texto reconhecido"

    assert recorded_command[0] == "tesseract"
    assert recorded_command[2:] == [
        "stdout",
        "-l",
        "por+eng",
        "--psm",
        "6",
    ]


def test_extract_returns_none_when_tesseract_returns_blank_text(
    tmp_path,
    monkeypatch,
):
    document, page, component = make_context(tmp_path)

    def fake_run(command, **kwargs):
        return CompletedProcess(
            args=command,
            returncode=0,
            stdout="   \n",
            stderr="",
        )

    monkeypatch.setattr(
        "edgar.ingestion.ocr_extraction.subprocess.run",
        fake_run,
    )

    extractor = TesseractOCRTextExtractor(
        storage_root=tmp_path,
    )

    assert extractor.extract(document, page, component) is None


def test_extract_raises_when_tesseract_fails(tmp_path, monkeypatch):
    document, page, component = make_context(tmp_path)

    def fake_run(command, **kwargs):
        return CompletedProcess(
            args=command,
            returncode=1,
            stdout="",
            stderr="OCR failure",
        )

    monkeypatch.setattr(
        "edgar.ingestion.ocr_extraction.subprocess.run",
        fake_run,
    )

    extractor = TesseractOCRTextExtractor(
        storage_root=tmp_path,
    )

    with pytest.raises(RuntimeError, match="OCR failure"):
        extractor.extract(
            document,
            page,
            component,
        )


def test_extract_rejects_page_image_dimension_mismatch(
    tmp_path,
):
    document, page, component = make_context(tmp_path)

    Image.new("RGB", (90, 80), "white").save(tmp_path / "page.png")

    extractor = TesseractOCRTextExtractor(
        storage_root=tmp_path,
    )

    with pytest.raises(RuntimeError):
        extractor.extract(
            document,
            page,
            component,
        )
