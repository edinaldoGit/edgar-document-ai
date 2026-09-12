from edgar.domain import Document, DocumentComponent, DocumentPage
from edgar.ingestion.contracts import (
    GeometryProcessor,
    LayoutAnalyzer,
)
from edgar.ingestion.crop_processing import VisualCropProcessor
from edgar.ingestion.table_structure_processing import (
    TableStructureProcessor,
)
from edgar.ingestion.text_processing import NativeTextProcessor
from edgar.ingestion.visual_description_processing import (
    VisualDescriptionProcessor,
)


class IngestionPipeline:
    def __init__(
        self,
        *,
        layout_analyzer: LayoutAnalyzer,
        geometry_processor: GeometryProcessor,
        crop_processor: VisualCropProcessor,
        text_processor: NativeTextProcessor,
        table_structure_processor: TableStructureProcessor,
        visual_description_processor: VisualDescriptionProcessor,
    ):
        self._layout_analyzer = layout_analyzer
        self._geometry_processor = geometry_processor
        self._crop_processor = crop_processor
        self._text_processor = text_processor
        self._table_structure_processor = table_structure_processor
        self._visual_description_processor = visual_description_processor

    def process_page(
        self,
        document: Document,
        page: DocumentPage,
    ) -> list[DocumentComponent]:
        components = self._layout_analyzer.analyze(page)

        components = self._geometry_processor.process(
            page,
            components,
        )

        components = self._crop_processor.process(
            page,
            components,
        )

        components = self._text_processor.process(
            document,
            page,
            components,
        )

        components = self._table_structure_processor.process(
            document,
            page,
            components,
        )

        components = self._visual_description_processor.process(
            components,
        )

        return components
