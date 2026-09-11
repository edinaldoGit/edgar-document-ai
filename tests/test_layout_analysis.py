from uuid import uuid4

from edgar.domain import ComponentType, DocumentPage
from edgar.ingestion.layout_analysis import DocLayoutYOLOAnalyzer


class FakeScalar:
    def __init__(self, value):
        self._value = value

    def item(self):
        return self._value


class FakeCoordinates:
    def __init__(self, values):
        self._values = values

    def __getitem__(self, index):
        assert index == 0
        return self

    def tolist(self):
        return self._values


class FakeDetection:
    def __init__(self, *, class_id, confidence, xyxy):
        self.cls = FakeScalar(class_id)
        self.conf = FakeScalar(confidence)
        self.xyxy = FakeCoordinates(xyxy)


class FakeResult:
    names = {
        0: "title",
        1: "plain text",
        3: "figure",
    }

    boxes = [
        FakeDetection(
            class_id=3,
            confidence=0.9471,
            xyxy=[466.11, 1068.22, 753.89, 1258.70],
        )
    ]


class FakeModel:
    def __init__(self):
        self.calls = []

    def predict(self, source, **kwargs):
        self.calls.append((source, kwargs))
        return [FakeResult()]


def test_analyze_converts_detection_to_document_component(tmp_path):
    image_path = tmp_path / "documents" / "example" / "pages" / "page_0001.png"
    image_path.parent.mkdir(parents=True)
    image_path.write_bytes(b"fake image")

    page = DocumentPage(
        doc_id=uuid4(),
        page_index=0,
        width=1221,
        height=1851,
        render_dpi=300,
        image_ref="documents/example/pages/page_0001.png",
    )

    model = FakeModel()

    analyzer = DocLayoutYOLOAnalyzer(
        model=model,
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

    assert model.calls == [
        (
            str(image_path),
            {
                "imgsz": 1024,
                "conf": 0.2,
                "device": "cpu",
            },
        )
    ]
