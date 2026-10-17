import argparse
import json
from pathlib import Path

from qdrant_client import QdrantClient, models

ROOT = Path(__file__).resolve().parents[2]

SOURCE = ROOT / "storage/experiments/20260919_182500_corpus_ingestion/qdrant"

DESTINATION = ROOT / "storage/experiments/e3_no_visual_description/qdrant"

REPORT = ROOT / "experiments/analysis/e3_index_build_report.json"

COLLECTION = "edgar-components"
VECTOR_SIZE = 1024
BATCH_SIZE = 200

EXPECTED_TOTAL = 7522
EXPECTED_REMOVED = 641
EXPECTED_RETAINED = 6881


def iter_points(client):
    offset = None

    while True:
        points, offset = client.scroll(
            collection_name=COLLECTION,
            limit=BATCH_SIZE,
            offset=offset,
            with_payload=True,
            with_vectors=True,
        )

        yield from points

        if offset is None:
            break


def should_remove(point):
    payload = point.payload or {}
    description = payload.get("visual_description")

    if not description:
        if not str(payload.get("text", "")).strip():
            raise RuntimeError(f"Blank retained representation: {point.id}")

        return False

    expected_text = "Visual description: " + description.strip()

    if (
        payload.get("component_type") != "figure"
        or str(payload.get("text", "")).strip() != expected_text
    ):
        raise RuntimeError(f"Unexpected visual representation: {point.id}")

    return True


def inspect_source(client):
    total = 0
    removed = 0
    retained = 0

    for point in iter_points(client):
        total += 1

        if point.vector is None or len(point.vector) != VECTOR_SIZE:
            raise RuntimeError(f"Invalid embedding: {point.id}")

        if should_remove(point):
            removed += 1
        else:
            retained += 1

    actual = (total, removed, retained)
    expected = (
        EXPECTED_TOTAL,
        EXPECTED_REMOVED,
        EXPECTED_RETAINED,
    )

    if actual != expected:
        raise RuntimeError(f"Unexpected counts: {actual}, expected {expected}")

    return {
        "source_components": total,
        "removed_visual_only_figures": removed,
        "retained_components": retained,
        "embedding_dimension": VECTOR_SIZE,
    }


def build_index(source):
    if DESTINATION.exists():
        raise RuntimeError(f"Destination already exists: {DESTINATION}")

    DESTINATION.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    target = QdrantClient(path=str(DESTINATION))

    try:
        target.create_collection(
            collection_name=COLLECTION,
            vectors_config=models.VectorParams(
                size=VECTOR_SIZE,
                distance=models.Distance.COSINE,
            ),
        )

        batch = []

        for point in iter_points(source):
            if should_remove(point):
                continue

            batch.append(
                models.PointStruct(
                    id=point.id,
                    vector=point.vector,
                    payload=point.payload,
                )
            )

            if len(batch) >= BATCH_SIZE:
                target.upsert(
                    collection_name=COLLECTION,
                    points=batch,
                    wait=True,
                )
                batch.clear()

        if batch:
            target.upsert(
                collection_name=COLLECTION,
                points=batch,
                wait=True,
            )

        count = target.count(
            collection_name=COLLECTION,
            exact=True,
        ).count

        if count != EXPECTED_RETAINED:
            raise RuntimeError(f"Incorrect target count: {count}")

        return count

    finally:
        target.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Create the E3 index after validating source data.",
    )
    args = parser.parse_args()

    source = QdrantClient(path=str(SOURCE))

    try:
        summary = inspect_source(source)

        print("SOURCE VALIDATION")
        print(json.dumps(summary, indent=2))

        if not args.execute:
            print()
            print("DRY RUN: no index created.")
            return

        count = build_index(source)

    finally:
        source.close()

    report = {
        "configuration": "E3",
        "definition": ("Fine-grained EDGAR without VLM-generated visual descriptions."),
        "source_index": str(SOURCE.relative_to(ROOT)),
        "target_index": str(DESTINATION.relative_to(ROOT)),
        "removed_component_type": "figure",
        "reused_embeddings": True,
        "new_embedding_calls": 0,
        "summary": summary,
        "indexed_components": count,
    }

    REPORT.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    print()
    print("E3 INDEX CREATED")
    print("Components:", count)
    print("Report:", REPORT)


if __name__ == "__main__":
    main()
