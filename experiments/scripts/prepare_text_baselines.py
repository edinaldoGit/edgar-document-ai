import argparse
import json
from collections import Counter
from math import ceil
from pathlib import Path
from uuid import NAMESPACE_URL, UUID, uuid5

import pymupdf

from edgar.domain import BoundingBox, ComponentType
from edgar.indexing.records import IndexRecord

ROOT = Path(__file__).resolve().parents[2]
DOCUMENTS_PATH = ROOT / "experiments/datasets/documents.json"
PDF_DIR = ROOT / "data/evaluation_dataset/processed"
OUTPUT_DIR = ROOT / "experiments/datasets/text_baselines"

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

EXPECTED_DOCUMENTS = {
    "calculus_001",
    "graphs_001",
    "physics_001",
    "statistics_001",
}


def chunk_spans(text):
    start = 0

    while start < len(text):
        end = min(start + CHUNK_SIZE, len(text))
        yield start, end

        if end == len(text):
            break

        start = end - CHUNK_OVERLAP


def make_record(
    *,
    configuration,
    doc_id,
    document_name,
    page_index,
    bbox,
    text,
    segment_index,
    start_char,
    end_char,
):
    component_id = uuid5(
        NAMESPACE_URL,
        (f"edgar:{configuration}:{doc_id}:{page_index}:{segment_index}"),
    )

    record = IndexRecord(
        component_id=component_id,
        doc_id=doc_id,
        page_index=page_index,
        component_type=ComponentType.PLAIN_TEXT,
        bbox=bbox,
        text=text,
    )

    return {
        "component_id": str(record.component_id),
        "doc_id": str(record.doc_id),
        "document": document_name,
        "page_index": record.page_index,
        "page_number": record.page_number,
        "component_type": record.component_type.value,
        "bbox": {
            "x1": bbox.x1,
            "y1": bbox.y1,
            "x2": bbox.x2,
            "y2": bbox.y2,
        },
        "bbox_scope": "full_page_reference_only",
        "segment_index": segment_index,
        "start_char": start_char,
        "end_char": end_char,
        "text": record.text,
    }


def prepare():
    documents = json.loads(DOCUMENTS_PATH.read_text(encoding="utf-8"))

    if len(documents) != 4 or {item["document_id"] for item in documents} != EXPECTED_DOCUMENTS:
        raise RuntimeError("Unexpected document mapping.")

    records = {"E1": [], "E2": []}
    counts = Counter()

    for document in documents:
        name = document["document_id"]
        doc_id = UUID(document["qdrant_doc_id"])
        pdf_path = PDF_DIR / document["filename"]

        with pymupdf.open(pdf_path) as pdf:
            if len(pdf) != document["pages"]:
                raise RuntimeError(f"Unexpected page count: {name}")

            for page_index, page in enumerate(pdf):
                counts["total_pages"] += 1
                text = page.get_text("text").strip()

                if not text:
                    counts["empty_pages"] += 1
                    continue

                counts["text_pages"] += 1

                bbox = BoundingBox(
                    x1=0,
                    y1=0,
                    x2=ceil(page.rect.width),
                    y2=ceil(page.rect.height),
                )

                spans = {
                    "E1": list(chunk_spans(text)),
                    "E2": [(0, len(text))],
                }

                for configuration, segments in spans.items():
                    for segment_index, (start, end) in enumerate(segments):
                        records[configuration].append(
                            make_record(
                                configuration=configuration,
                                doc_id=doc_id,
                                document_name=name,
                                page_index=page_index,
                                bbox=bbox,
                                text=text[start:end],
                                segment_index=segment_index,
                                start_char=start,
                                end_char=end,
                            )
                        )

                    counts[f"{configuration}_{name}"] += len(segments)

    counts["E1_records"] = len(records["E1"])
    counts["E2_records"] = len(records["E2"])

    if counts["total_pages"] != 578:
        raise RuntimeError("Unexpected corpus page count.")

    if counts["text_pages"] != 570:
        raise RuntimeError("Unexpected textual page count.")

    if counts["E2_records"] != 570:
        raise RuntimeError("Unexpected E2 record count.")

    for configuration in records:
        ids = [record["component_id"] for record in records[configuration]]
        if len(ids) != len(set(ids)):
            raise RuntimeError(f"Duplicate IDs in {configuration}")

    return records, counts


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    records, counts = prepare()

    print("=== TEXT BASELINES ===")

    for key, value in sorted(counts.items()):
        print(f"{key}: {value}")

    print(f"Chunk size: {CHUNK_SIZE}")
    print(f"Chunk overlap: {CHUNK_OVERLAP}")
    print("Geometry: full-page reference only")

    if not args.write:
        print("\nDRY RUN: no files created.")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for configuration, items in records.items():
        path = OUTPUT_DIR / f"{configuration.lower()}_records.jsonl"

        with path.open("x", encoding="utf-8") as output:
            for item in items:
                output.write(json.dumps(item, ensure_ascii=False) + "\n")

        print("Created:", path)


if __name__ == "__main__":
    main()
