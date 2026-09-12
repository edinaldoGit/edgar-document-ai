from uuid import uuid4

from edgar.domain import (
    BoundingBox,
    ComponentType,
    Document,
    DocumentComponent,
    DocumentPage,
)
from edgar.ingestion.pipeline import IngestionPipeline


class RecordingLayoutAnalyzer:
    def __init__(self, events, component):
        self.events = events
        self.component = component

    def analyze(self, page):
        self.events.append("layout")
        return [self.component]


class RecordingGeometryProcessor:
    def __init__(self, events):
        self.events = events

    def process(self, page, components):
        self.events.append("geometry")
        return components


class RecordingCropProcessor:
    def __init__(self, events):
        self.events = events

    def process(self, page, components):
        self.events.append("crop")
        return components


class RecordingTextProcessor:
    def __init__(self, events):
        self.events = events

    def process(self, document, page, components):
        self.events.append("text")
        return components


class RecordingTableStructureProcessor:
    def __init__(self, events):
        self.events = events

    def process(self, document, page, components):
        self.events.append("table_structure")
        return components


class RecordingVisualDescriptionProcessor:
    def __init__(self, events):
        self.events = events

    def process(self, components):
        self.events.append("visual_description")
        return components


def test_processes_page_in_ingestion_order():
    events = []
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

    component = DocumentComponent(
        doc_id=doc_id,
        page_index=0,
        component_type=ComponentType.FIGURE,
        bbox=BoundingBox(
            x1=10,
            y1=20,
            x2=100,
            y2=200,
        ),
    )

    pipeline = IngestionPipeline(
        layout_analyzer=RecordingLayoutAnalyzer(
            events,
            component,
        ),
        geometry_processor=RecordingGeometryProcessor(
            events,
        ),
        crop_processor=RecordingCropProcessor(
            events,
        ),
        text_processor=RecordingTextProcessor(
            events,
        ),
        table_structure_processor=RecordingTableStructureProcessor(
            events,
        ),
        visual_description_processor=RecordingVisualDescriptionProcessor(
            events,
        ),
    )

    result = pipeline.process_page(
        document,
        page,
    )

    assert result == [component]

    assert events == [
        "layout",
        "geometry",
        "crop",
        "text",
        "table_structure",
        "visual_description",
    ]
