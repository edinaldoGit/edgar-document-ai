from pathlib import Path

from qdrant_client import QdrantClient

from edgar.generation.pipeline import AnsweringPipeline
from edgar.indexing.document_runner import DocumentIndexingRunner
from edgar.indexing.pipeline import IndexingPipeline
from edgar.infrastructure.modal_answer_generation_client import ModalAnswerGenerationClient
from edgar.infrastructure.modal_answer_generator import ModalAnswerGenerator
from edgar.infrastructure.modal_embedding_client import ModalEmbeddingClient
from edgar.infrastructure.modal_layout_analyzer import ModalLayoutAnalyzer
from edgar.infrastructure.modal_layout_client import ModalLayoutClient
from edgar.infrastructure.modal_text_embedder import ModalTextEmbedder
from edgar.infrastructure.modal_visual_describer import ModalVisualDescriber
from edgar.infrastructure.modal_visual_description_client import (
    ModalVisualDescriptionClient,
)
from edgar.infrastructure.qdrant_vector_store import QdrantVectorStore
from edgar.ingestion.crop_processing import VisualCropProcessor
from edgar.ingestion.cropping import ComponentCropper
from edgar.ingestion.document_runner import DocumentIngestionRunner
from edgar.ingestion.fallback_text_extraction import FallbackTextExtractor
from edgar.ingestion.geometry_processing import IdentityGeometryProcessor
from edgar.ingestion.ocr_extraction import TesseractOCRTextExtractor
from edgar.ingestion.pipeline import IngestionPipeline
from edgar.ingestion.rasterization import PyMuPDFRasterizer
from edgar.ingestion.table_structure_extraction import (
    PyMuPDFTableStructureExtractor,
)
from edgar.ingestion.table_structure_processing import TableStructureProcessor
from edgar.ingestion.text_extraction import PyMuPDFTextExtractor
from edgar.ingestion.text_processing import NativeTextProcessor
from edgar.ingestion.visual_description_processing import (
    VisualDescriptionProcessor,
)
from edgar.retrieval.semantic import SemanticRetriever


def build_ingestion_runner(
    *,
    storage_root: str | Path,
) -> DocumentIngestionRunner:
    storage_root = Path(storage_root)

    rasterizer = PyMuPDFRasterizer(
        storage_root=storage_root,
    )

    layout_analyzer = ModalLayoutAnalyzer(
        client=ModalLayoutClient(),
        storage_root=storage_root,
    )

    crop_processor = VisualCropProcessor(
        cropper=ComponentCropper(
            storage_root=storage_root,
        ),
    )

    text_extractor = FallbackTextExtractor(
        primary=PyMuPDFTextExtractor(
            storage_root=storage_root,
        ),
        fallback=TesseractOCRTextExtractor(
            storage_root=storage_root,
        ),
    )

    pipeline = IngestionPipeline(
        layout_analyzer=layout_analyzer,
        geometry_processor=IdentityGeometryProcessor(),
        crop_processor=crop_processor,
        text_processor=NativeTextProcessor(
            extractor=text_extractor,
        ),
        table_structure_processor=TableStructureProcessor(
            extractor=PyMuPDFTableStructureExtractor(
                storage_root=storage_root,
            ),
        ),
        visual_description_processor=VisualDescriptionProcessor(
            describer=ModalVisualDescriber(
                client=ModalVisualDescriptionClient(),
                storage_root=storage_root,
            ),
        ),
    )

    return DocumentIngestionRunner(
        rasterizer=rasterizer,
        pipeline=pipeline,
    )


def build_indexing_runner(
    *,
    storage_root: str | Path,
    qdrant_path: str | Path | None = None,
) -> DocumentIndexingRunner:
    ingestion_runner = build_ingestion_runner(
        storage_root=storage_root,
    )

    embedder = ModalTextEmbedder(
        client=ModalEmbeddingClient(),
    )

    if qdrant_path is None:
        client = QdrantClient(":memory:")
    else:
        client = QdrantClient(
            path=str(qdrant_path),
        )

    vector_store = QdrantVectorStore(
        client=client,
    )

    indexing_pipeline = IndexingPipeline(
        embedder=embedder,
        store=vector_store,
    )

    return DocumentIndexingRunner(
        ingestion_runner=ingestion_runner,
        indexing_pipeline=indexing_pipeline,
    )


def build_retriever(
    *,
    qdrant_path: str | Path,
) -> SemanticRetriever:
    embedder = ModalTextEmbedder(
        client=ModalEmbeddingClient(),
    )

    vector_store = QdrantVectorStore(
        client=QdrantClient(
            path=str(qdrant_path),
        ),
    )

    return SemanticRetriever(
        embedder=embedder,
        searcher=vector_store,
    )


def build_answering_pipeline(
    *,
    qdrant_path: str | Path,
    max_new_tokens: int = 256,
) -> AnsweringPipeline:
    retriever = build_retriever(
        qdrant_path=qdrant_path,
    )

    generator = ModalAnswerGenerator(
        client=ModalAnswerGenerationClient(),
        max_new_tokens=max_new_tokens,
    )

    return AnsweringPipeline(
        retriever=retriever,
        generator=generator,
    )
