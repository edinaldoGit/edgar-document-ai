from edgar.indexing.contracts import TextEmbedder
from edgar.indexing.embedded_records import EmbeddedIndexRecord
from edgar.indexing.records import IndexRecord


def embed_index_records(
    records: list[IndexRecord],
    *,
    embedder: TextEmbedder,
) -> list[EmbeddedIndexRecord]:
    if not records:
        return []

    embeddings = embedder.embed([record.text for record in records])

    if len(embeddings) != len(records):
        raise RuntimeError("Embedding count does not match index record count.")

    return [
        EmbeddedIndexRecord(
            record=record,
            embedding=tuple(embedding),
        )
        for record, embedding in zip(
            records,
            embeddings,
            strict=True,
        )
    ]
