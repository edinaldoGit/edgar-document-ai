from uuid import UUID

from qdrant_client import QdrantClient, models

from edgar.domain import BoundingBox, ComponentType
from edgar.indexing.embedded_records import EmbeddedIndexRecord
from edgar.retrieval.results import RetrievedEvidence

DEFAULT_COLLECTION_NAME = "edgar-components"
DEFAULT_VECTOR_SIZE = 1024


class QdrantVectorStore:
    def __init__(
        self,
        *,
        client: QdrantClient,
        collection_name: str = DEFAULT_COLLECTION_NAME,
        vector_size: int = DEFAULT_VECTOR_SIZE,
    ):
        if not collection_name.strip():
            raise ValueError("Collection name must not be blank.")

        if vector_size <= 0:
            raise ValueError("Vector size must be positive.")

        self._client = client
        self._collection_name = collection_name
        self._vector_size = vector_size

    def ensure_collection(self) -> None:
        if self._client.collection_exists(
            collection_name=self._collection_name,
        ):
            return

        self._client.create_collection(
            collection_name=self._collection_name,
            vectors_config=models.VectorParams(
                size=self._vector_size,
                distance=models.Distance.COSINE,
            ),
        )

    def upsert(
        self,
        records: list[EmbeddedIndexRecord],
    ) -> None:
        if not records:
            return

        for record in records:
            if record.dimension != self._vector_size:
                raise ValueError(
                    "Embedding dimension does not match the Qdrant collection vector size."
                )

        self.ensure_collection()

        points = [
            models.PointStruct(
                id=str(record.record.component_id),
                vector=list(record.embedding),
                payload=_build_payload(record),
            )
            for record in records
        ]

        self._client.upsert(
            collection_name=self._collection_name,
            wait=True,
            points=points,
        )

    def search(
        self,
        query_embedding: list[float],
        *,
        limit: int = 5,
        doc_id: UUID | None = None,
    ) -> list[RetrievedEvidence]:
        if len(query_embedding) != self._vector_size:
            raise ValueError(
                "Query embedding dimension does not match the Qdrant collection vector size."
            )

        if limit <= 0:
            raise ValueError("Search limit must be positive.")

        if not self._client.collection_exists(
            collection_name=self._collection_name,
        ):
            return []

        query_filter = None

        if doc_id is not None:
            query_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="doc_id",
                        match=models.MatchValue(
                            value=str(doc_id),
                        ),
                    )
                ]
            )

        response = self._client.query_points(
            collection_name=self._collection_name,
            query=query_embedding,
            query_filter=query_filter,
            limit=limit,
            with_payload=True,
        )

        return [_point_to_evidence(point) for point in response.points]


def _build_payload(
    embedded_record: EmbeddedIndexRecord,
) -> dict:
    record = embedded_record.record

    payload = {
        "component_id": str(record.component_id),
        "doc_id": str(record.doc_id),
        "page_index": record.page_index,
        "page_number": record.page_number,
        "component_type": record.component_type.value,
        "bbox": {
            "x1": record.bbox.x1,
            "y1": record.bbox.y1,
            "x2": record.bbox.x2,
            "y2": record.bbox.y2,
        },
        "text": record.text,
    }

    optional_fields = {
        "text_extracted": record.text_extracted,
        "visual_description": record.visual_description,
        "crop_ref": record.crop_ref,
    }

    payload.update({key: value for key, value in optional_fields.items() if value is not None})

    return payload


def _point_to_evidence(
    point: models.ScoredPoint,
) -> RetrievedEvidence:
    payload = point.payload or {}
    bbox = payload["bbox"]

    return RetrievedEvidence(
        component_id=UUID(payload["component_id"]),
        doc_id=UUID(payload["doc_id"]),
        page_index=int(payload["page_index"]),
        component_type=ComponentType(payload["component_type"]),
        bbox=BoundingBox(
            x1=int(bbox["x1"]),
            y1=int(bbox["y1"]),
            x2=int(bbox["x2"]),
            y2=int(bbox["y2"]),
        ),
        text=str(payload["text"]),
        score=float(point.score),
        text_extracted=payload.get("text_extracted"),
        visual_description=payload.get("visual_description"),
        crop_ref=payload.get("crop_ref"),
    )
