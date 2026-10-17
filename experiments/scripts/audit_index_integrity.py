import json
from collections import Counter
from pathlib import Path

from PIL import Image
from qdrant_client import QdrantClient

ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT = ROOT / "storage/experiments/20260919_182500_corpus_ingestion"
DOCUMENTS = ROOT / "experiments/datasets/documents.json"
OUTPUT = ROOT / "experiments/analysis/index_integrity_audit.json"

COLLECTION = "edgar-components"


def image_size(path: Path):
    try:
        with Image.open(path) as image:
            return image.size
    except (OSError, ValueError):
        return None


def main():
    documents = json.loads(DOCUMENTS.read_text(encoding="utf-8"))

    by_uuid = {item["qdrant_doc_id"]: item for item in documents}

    client = QdrantClient(path=str(SNAPSHOT / "qdrant"))

    counts = Counter()
    issues = Counter()
    examples = {}
    page_cache = {}
    crop_count = 0
    checked = 0
    offset = None

    def issue(kind, component_id, detail):
        issues[kind] += 1
        examples.setdefault(kind, [])

        if len(examples[kind]) < 10:
            examples[kind].append(
                {
                    "component_id": component_id,
                    "detail": str(detail),
                }
            )

    while True:
        points, offset = client.scroll(
            collection_name=COLLECTION,
            limit=500,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )

        for point in points:
            checked += 1
            payload = point.payload or {}
            component_id = str(payload.get("component_id", point.id))
            doc_id = str(payload.get("doc_id", ""))

            counts[doc_id] += 1

            if component_id != str(point.id):
                issue(
                    "component_id_mismatch",
                    component_id,
                    point.id,
                )

            document = by_uuid.get(doc_id)

            if document is None:
                issue("unknown_document", component_id, doc_id)
                continue

            try:
                page_index = int(payload["page_index"])
                page_number = int(payload["page_number"])
                bbox = payload["bbox"]

                x1, y1, x2, y2 = (int(bbox[key]) for key in ("x1", "y1", "x2", "y2"))
            except (KeyError, TypeError, ValueError):
                issue(
                    "invalid_payload",
                    component_id,
                    "Missing or invalid page/bbox fields",
                )
                continue

            if page_number != page_index + 1 or not 1 <= page_number <= document["pages"]:
                issue(
                    "invalid_page_number",
                    component_id,
                    page_number,
                )

            page_key = (doc_id, page_number)

            if page_key not in page_cache:
                page_path = (
                    SNAPSHOT / "documents" / doc_id / "pages" / f"page_{page_number:04d}.png"
                )
                page_cache[page_key] = image_size(page_path)

            dimensions = page_cache[page_key]

            if dimensions is None:
                issue(
                    "missing_or_invalid_page_image",
                    component_id,
                    page_key,
                )
            else:
                width, height = dimensions

                if not (0 <= x1 < x2 <= width and 0 <= y1 < y2 <= height):
                    issue(
                        "bbox_out_of_bounds",
                        component_id,
                        (x1, y1, x2, y2, width, height),
                    )

            crop_ref = payload.get("crop_ref")

            if crop_ref:
                crop_count += 1
                crop_path = Path(crop_ref)

                if crop_path.is_absolute() or not (SNAPSHOT / crop_path).resolve().is_relative_to(
                    SNAPSHOT.resolve()
                ):
                    issue(
                        "invalid_crop_path",
                        component_id,
                        crop_ref,
                    )
                    continue

                if crop_path.parts[:2] != ("documents", doc_id):
                    issue(
                        "crop_document_mismatch",
                        component_id,
                        crop_ref,
                    )

                crop_dimensions = image_size(SNAPSHOT / crop_path)

                if crop_dimensions is None:
                    issue(
                        "missing_or_invalid_crop",
                        component_id,
                        crop_ref,
                    )
                elif crop_dimensions != (
                    x2 - x1,
                    y2 - y1,
                ):
                    issue(
                        "crop_dimension_mismatch",
                        component_id,
                        {
                            "actual": crop_dimensions,
                            "expected": (
                                x2 - x1,
                                y2 - y1,
                            ),
                        },
                    )

        if offset is None:
            break

    report = {
        "source_snapshot": ("20260919_182500_corpus_ingestion"),
        "total_components": checked,
        "unique_pages_referenced": len(page_cache),
        "components_with_crop": crop_count,
        "components_by_doc_id": dict(counts),
        "issue_counts": dict(issues),
        "issue_examples": examples,
        "scope": (
            "Physical file availability, metadata consistency, "
            "bbox boundaries and crop dimensions. "
            "Does not validate semantic correctness."
        ),
    }

    OUTPUT.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    print("Componentes auditados:", checked)
    print("Páginas referenciadas:", len(page_cache))
    print("Componentes com crop:", crop_count)
    print("Problemas encontrados:", sum(issues.values()))
    print("Detalhamento:", dict(issues))
    print("Relatório:", OUTPUT)


if __name__ == "__main__":
    main()
