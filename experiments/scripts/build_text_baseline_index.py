import argparse
import json
from pathlib import Path
from time import perf_counter

from qdrant_client import QdrantClient, models

from edgar.infrastructure.modal_embedding_client import ModalEmbeddingClient
from edgar.infrastructure.modal_text_embedder import ModalTextEmbedder

ROOT = Path(__file__).resolve().parents[2]
COLLECTION = "edgar-components"
VECTOR_SIZE = 1024

CONFIGURATIONS = {
    "e1": {
        "expected": 1339,
        "batch_size": 32,
        "directory": "e1_text_chunks",
    },
    "e2": {
        "expected": 570,
        "batch_size": 4,
        "directory": "e2_page_text",
    },
}


def load_records(baseline, expected):
    path = ROOT / "experiments/datasets/text_baselines" / f"{baseline}_records.jsonl"

    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]

    if len(records) != expected:
        raise RuntimeError(f"Unexpected record count: {len(records)}")

    ids = [record["component_id"] for record in records]

    if len(ids) != len(set(ids)):
        raise RuntimeError("Duplicate component IDs.")

    for record in records:
        if not record["text"].strip():
            raise RuntimeError("Blank text found.")

        if record["component_type"] != "plain_text":
            raise RuntimeError("Unexpected component type.")

        if record["bbox_scope"] != "full_page_reference_only":
            raise RuntimeError("Unexpected geometry scope.")

        if record["page_number"] != record["page_index"] + 1:
            raise RuntimeError("Inconsistent page numbering.")

    return path, records


def ensure_collection(client):
    if client.collection_exists(COLLECTION):
        config = client.get_collection(COLLECTION).config.params.vectors

        if (
            not isinstance(config, models.VectorParams)
            or config.size != VECTOR_SIZE
            or config.distance != models.Distance.COSINE
        ):
            raise RuntimeError("Incompatible existing collection.")

        return

    client.create_collection(
        collection_name=COLLECTION,
        vectors_config=models.VectorParams(
            size=VECTOR_SIZE,
            distance=models.Distance.COSINE,
        ),
    )


def index_records(records, destination, batch_size):
    destination.parent.mkdir(parents=True, exist_ok=True)

    client = QdrantClient(path=str(destination))
    embedder = ModalTextEmbedder(client=ModalEmbeddingClient())

    new_embeddings = 0
    reused_embeddings = 0

    try:
        ensure_collection(client)

        total_batches = (len(records) + batch_size - 1) // batch_size

        for batch_number, start in enumerate(
            range(0, len(records), batch_size),
            start=1,
        ):
            batch = records[start : start + batch_size]

            existing = client.retrieve(
                collection_name=COLLECTION,
                ids=[record["component_id"] for record in batch],
                with_payload=True,
                with_vectors=False,
            )

            expected_by_id = {record["component_id"]: record for record in batch}

            existing_ids = set()

            for point in existing:
                point_id = str(point.id)
                if point.payload != expected_by_id[point_id]:
                    raise RuntimeError(f"Existing record differs from dataset: {point_id}")
                existing_ids.add(point_id)

            pending = [record for record in batch if record["component_id"] not in existing_ids]

            reused_embeddings += len(existing_ids)

            if pending:
                embeddings = embedder.embed([record["text"] for record in pending])

                if len(embeddings) != len(pending):
                    raise RuntimeError("Embedding count mismatch.")

                if any(len(vector) != VECTOR_SIZE for vector in embeddings):
                    raise RuntimeError("Invalid embedding dimension.")

                points = [
                    models.PointStruct(
                        id=record["component_id"],
                        vector=vector,
                        payload=record,
                    )
                    for record, vector in zip(
                        pending,
                        embeddings,
                        strict=True,
                    )
                ]

                client.upsert(
                    collection_name=COLLECTION,
                    points=points,
                    wait=True,
                )

                new_embeddings += len(pending)

            if batch_number % 10 == 0 or batch_number == total_batches:
                print(
                    f"[{batch_number}/{total_batches}] "
                    f"novos={new_embeddings} "
                    f"reutilizados={reused_embeddings}",
                    flush=True,
                )

        final_count = client.count(
            collection_name=COLLECTION,
            exact=True,
        ).count

        if final_count != len(records):
            raise RuntimeError(f"Final count mismatch: {final_count}")

        return {
            "indexed_records": final_count,
            "new_embeddings": new_embeddings,
            "reused_embeddings": reused_embeddings,
        }

    finally:
        client.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--baseline",
        choices=("e1", "e2"),
        required=True,
    )
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()

    config = CONFIGURATIONS[args.baseline]

    source, records = load_records(
        args.baseline,
        config["expected"],
    )

    destination = ROOT / "storage/experiments" / config["directory"] / "qdrant"

    print("Baseline:", args.baseline.upper())
    print("Records:", len(records))
    print("Batch size:", config["batch_size"])
    print("Embedding model: BAAI/bge-m3")
    print("Vector size:", VECTOR_SIZE)
    print("Destination:", destination)

    if not args.execute:
        print("\nDRY RUN: no embeddings or index created.")
        return

    start = perf_counter()

    summary = index_records(
        records,
        destination,
        config["batch_size"],
    )

    report = {
        "baseline": args.baseline.upper(),
        "source_records": str(source.relative_to(ROOT)),
        "index_path": str(destination.relative_to(ROOT)),
        "collection": COLLECTION,
        "embedding_model": "BAAI/bge-m3",
        "embedding_dimension": VECTOR_SIZE,
        "normalized_embeddings": True,
        "distance": "cosine",
        "batch_size": config["batch_size"],
        "bbox_scope": "full_page_reference_only",
        "elapsed_seconds": round(perf_counter() - start, 3),
        "summary": summary,
    }

    report_path = ROOT / "experiments/analysis" / f"{args.baseline}_index_build_report.json"

    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print("\nINDEX COMPLETED")
    print(json.dumps(summary, indent=2))
    print("Report:", report_path)


if __name__ == "__main__":
    main()
