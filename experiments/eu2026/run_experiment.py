import json
from pathlib import Path

import pymupdf
from qdrant_client import QdrantClient

from edgar.application.bootstrap import (
    build_ingestion_runner,
)
from edgar.domain import Document
from edgar.generation.pipeline import AnsweringPipeline
from edgar.indexing.pipeline import IndexingPipeline
from edgar.infrastructure.modal_answer_generation_client import (
    ModalAnswerGenerationClient,
)
from edgar.infrastructure.modal_answer_generator import (
    ModalAnswerGenerator,
)
from edgar.infrastructure.modal_embedding_client import (
    ModalEmbeddingClient,
)
from edgar.infrastructure.modal_text_embedder import (
    ModalTextEmbedder,
)
from edgar.infrastructure.qdrant_vector_store import (
    QdrantVectorStore,
)
from edgar.retrieval.semantic import SemanticRetriever

BASE = Path("experiments/eu2026")

PDF_PATH = BASE / "input/physics_vectors_sample.pdf"

STORAGE = BASE / "output/storage"

QDRANT_PATH = BASE / "output/qdrant"


def component_to_dict(component):
    return {
        "page": component.page_number,
        "type": component.component_type.value,
        "text": component.text_extracted,
        "visual_description": component.visual_description,
        "crop_ref": component.crop_ref,
        "bbox": {
            "x1": component.bbox.x1,
            "y1": component.bbox.y1,
            "x2": component.bbox.x2,
            "y2": component.bbox.y2,
        },
    }


def main():
    doc = pymupdf.open(PDF_PATH)

    document = Document(
        filename=PDF_PATH.name,
        source_ref=str(PDF_PATH.resolve()),
        page_count=doc.page_count,
    )

    # 1. Ingestão
    ingestion_runner = build_ingestion_runner(
        storage_root=STORAGE,
    )

    components = ingestion_runner.run(document)

    print("Componentes:", len(components))

    BASE.joinpath("output/components.json").write_text(
        json.dumps(
            [component_to_dict(c) for c in components],
            indent=2,
            ensure_ascii=False,
        )
    )

    # 2. Indexação
    embedder = ModalTextEmbedder(
        client=ModalEmbeddingClient(),
    )

    store = QdrantVectorStore(
        client=QdrantClient(
            path=str(QDRANT_PATH),
        ),
    )

    indexing_pipeline = IndexingPipeline(
        embedder=embedder,
        store=store,
    )

    records = indexing_pipeline.index(
        components,
    )

    print("Registros indexados:", len(records))

    # 3. Recuperação + geração

    retriever = SemanticRetriever(
        embedder=embedder,
        searcher=store,
    )

    generator = ModalAnswerGenerator(
        ModalAnswerGenerationClient(),
    )

    answering_pipeline = AnsweringPipeline(
        retriever=retriever,
        generator=generator,
    )

    question = (
        "Explique o conceito apresentado nas figuras desta seção "
        "e relacione com a explicação textual."
    )

    result = answering_pipeline.answer(
        question,
        doc_id=document.doc_id,
        limit=5,
    )

    evidences_output = [
        {
            "page": evidence.page_number,
            "type": evidence.component_type.value,
            "score": evidence.score,
            "text": evidence.text,
            "visual_description": evidence.visual_description,
            "crop_ref": evidence.crop_ref,
        }
        for evidence in result.evidences
    ]

    BASE.joinpath("output/retrieval.json").write_text(
        json.dumps(
            evidences_output,
            indent=2,
            ensure_ascii=False,
        )
    )

    output = {
        "question": result.question,
        "answer": result.answer,
        "evidences": evidences_output,
    }

    BASE.joinpath("output/answers.json").write_text(
        json.dumps(
            output,
            indent=2,
            ensure_ascii=False,
        )
    )

    print("Resposta:")
    print(result.answer)


if __name__ == "__main__":
    main()
