from uuid import UUID

import pytest

from edgar.domain import Document


def test_document_creation():
    document = Document(
        filename="example.pdf",
        source_ref="documents/example/original.pdf",
        page_count=10,
    )

    assert document.filename == "example.pdf"
    assert document.source_ref == "documents/example/original.pdf"
    assert document.page_count == 10
    assert isinstance(document.doc_id, UUID)


def test_documents_receive_different_ids():
    first = Document(
        filename="first.pdf",
        source_ref="documents/first/original.pdf",
        page_count=10,
    )

    second = Document(
        filename="second.pdf",
        source_ref="documents/second/original.pdf",
        page_count=10,
    )

    assert first.doc_id != second.doc_id


def test_document_rejects_empty_filename():
    with pytest.raises(ValueError):
        Document(
            filename="   ",
            source_ref="documents/example/original.pdf",
            page_count=10,
        )


def test_document_rejects_empty_source_reference():
    with pytest.raises(ValueError):
        Document(
            filename="example.pdf",
            source_ref="   ",
            page_count=10,
        )


@pytest.mark.parametrize("page_count", [0, -1])
def test_document_rejects_invalid_page_count(page_count):
    with pytest.raises(ValueError):
        Document(
            filename="example.pdf",
            source_ref="documents/example/original.pdf",
            page_count=page_count,
        )
