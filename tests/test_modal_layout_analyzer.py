from uuid import uuid4

import pytest

from edgar.domain import ComponentType, DocumentPage
from edgar.infrastructure.modal_layout_analyzer import ModalLayoutAnalyzer


class FakeModalLayoutClient:
    def analyze_image(self, image_bytes):
        assert image_bytes == b"fake image"

        return {
            "predict_seconds": 0.1,
            "original_shape": (1851, 1221),
            "detections": [
                {
                    "class_name": "figure",
                    "confidence": 0.9471,
                    "xyxy": [466.11, 1068.22, 753.89, 1258.70],
                }
            ],
        }


def test_analyze_converts_remote_detection_to_document_component(tmp_path):
    image_path = tmp_path / "page.png"
    image_path.write_bytes(b"fake image")

    page = DocumentPage(
        doc_id=uuid4(),
        page_index=0,
        width=1221,
        height=1851,
        render_dpi=300,
        image_ref="page.png",
    )

    analyzer = ModalLayoutAnalyzer(
        client=FakeModalLayoutClient(),
        storage_root=tmp_path,
    )

    components = analyzer.analyze(page)

    assert len(components) == 1

    component = components[0]

    assert component.doc_id == page.doc_id
    assert component.page_index == 0
    assert component.component_type == ComponentType.FIGURE
    assert component.detection_confidence == 0.9471

    assert component.bbox.x1 == 466
    assert component.bbox.y1 == 1068
    assert component.bbox.x2 == 754
    assert component.bbox.y2 == 1259


def test_analyze_rejects_remote_dimension_mismatch(tmp_path):
    image_path = tmp_path / "page.png"
    image_path.write_bytes(b"fake image")

    page = DocumentPage(
        doc_id=uuid4(),
        page_index=0,
        width=1000,
        height=1851,
        render_dpi=300,
        image_ref="page.png",
    )

    analyzer = ModalLayoutAnalyzer(
        client=FakeModalLayoutClient(),
        storage_root=tmp_path,
    )

    with pytest.raises(RuntimeError):
        analyzer.analyze(page)


def test_analyze_rejects_missing_page_image(tmp_path):
    page = DocumentPage(
        doc_id=uuid4(),
        page_index=0,
        width=1221,
        height=1851,
        render_dpi=300,
        image_ref="missing.png",
    )

    analyzer = ModalLayoutAnalyzer(
        client=FakeModalLayoutClient(),
        storage_root=tmp_path,
    )

    with pytest.raises(FileNotFoundError):
        analyzer.analyze(page)
