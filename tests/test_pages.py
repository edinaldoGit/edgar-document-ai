from uuid import uuid4

import pytest

from edgar.domain import DocumentPage


def test_document_page_creation():
    doc_id = uuid4()

    page = DocumentPage(
        doc_id=doc_id,
        page_index=0,
        width=2480,
        height=3508,
        render_dpi=300,
        image_ref="documents/example/pages/page_0001.png",
    )

    assert page.doc_id == doc_id
    assert page.page_index == 0
    assert page.page_number == 1
    assert page.width == 2480
    assert page.height == 3508
    assert page.render_dpi == 300
    assert page.dimensions == (2480, 3508)


def test_document_page_rejects_negative_page_index():
    with pytest.raises(ValueError):
        DocumentPage(
            doc_id=uuid4(),
            page_index=-1,
            width=2480,
            height=3508,
            render_dpi=300,
            image_ref="page.png",
        )


@pytest.mark.parametrize(
    ("width", "height"),
    [
        (0, 100),
        (-1, 100),
        (100, 0),
        (100, -1),
    ],
)
def test_document_page_rejects_invalid_dimensions(width, height):
    with pytest.raises(ValueError):
        DocumentPage(
            doc_id=uuid4(),
            page_index=0,
            width=width,
            height=height,
            render_dpi=300,
            image_ref="page.png",
        )


def test_document_page_rejects_invalid_dpi():
    with pytest.raises(ValueError):
        DocumentPage(
            doc_id=uuid4(),
            page_index=0,
            width=2480,
            height=3508,
            render_dpi=0,
            image_ref="page.png",
        )


def test_document_page_rejects_empty_image_reference():
    with pytest.raises(ValueError):
        DocumentPage(
            doc_id=uuid4(),
            page_index=0,
            width=2480,
            height=3508,
            render_dpi=300,
            image_ref="   ",
        )
