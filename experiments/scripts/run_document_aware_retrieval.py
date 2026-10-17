import json
from datetime import datetime
from pathlib import Path
from time import perf_counter

from edgar.application.bootstrap import build_retriever

ROOT = Path(__file__).resolve().parents[2]
QUERY_DIR = ROOT / "data/evaluation_dataset/queries"
DOCUMENTS_PATH = ROOT / "experiments/datasets/documents.json"

QDRANT_PATH = ROOT / "storage/experiments" / "20260919_182500_corpus_ingestion/qdrant"

RUNS_ROOT = ROOT / "experiments/runs"
TOP_K = 20
CUTOFFS = (5, 10, 20)


def load_dataset():
    documents = json.loads(DOCUMENTS_PATH.read_text(encoding="utf-8"))

    document_ids = {item["document_id"]: item["qdrant_doc_id"] for item in documents}

    queries = []

    for path in sorted(QUERY_DIR.glob("*_queries.json")):
        queries.extend(json.loads(path.read_text(encoding="utf-8")))

    if len(queries) != 26:
        raise RuntimeError(f"Expected 26 queries, found {len(queries)}.")

    if len({query["id"] for query in queries}) != len(queries):
        raise RuntimeError("Duplicate query IDs.")

    for query in queries:
        if query["document"] not in document_ids:
            raise RuntimeError(f"Unknown document: {query['document']}")

    return document_ids, queries


def first_hit_rank(
    evidences,
    *,
    expected_doc_id,
    expected_page,
    expected_type=None,
):
    for rank, evidence in enumerate(evidences, start=1):
        if str(evidence.doc_id) != expected_doc_id:
            continue

        if evidence.page_number != expected_page:
            continue

        if expected_type is not None and evidence.component_type.value != expected_type:
            continue

        return rank

    return None


def main():
    document_ids, queries = load_dataset()
    retriever = build_retriever(qdrant_path=QDRANT_PATH)

    results = []
    start = perf_counter()

    for query in queries:
        gold = query["expected_evidence"]
        expected_doc_id = document_ids[query["document"]]

        query_start = perf_counter()

        evidences = retriever.retrieve(
            query["question"],
            limit=TOP_K,
        )

        query_elapsed = perf_counter() - query_start

        page_rank = first_hit_rank(
            evidences,
            expected_doc_id=expected_doc_id,
            expected_page=gold["page"],
        )

        component_rank = first_hit_rank(
            evidences,
            expected_doc_id=expected_doc_id,
            expected_page=gold["page"],
            expected_type=gold["component_type"],
        )

        retrieved = []

        for rank, evidence in enumerate(evidences, start=1):
            retrieved.append(
                {
                    "rank": rank,
                    "component_id": str(evidence.component_id),
                    "doc_id": str(evidence.doc_id),
                    "page_number": evidence.page_number,
                    "component_type": evidence.component_type.value,
                    "score": evidence.score,
                }
            )

        results.append(
            {
                "id": query["id"],
                "document": query["document"],
                "question": query["question"],
                "expected_doc_id": expected_doc_id,
                "expected_page": gold["page"],
                "expected_component_type": gold["component_type"],
                "page_first_rank": page_rank,
                "component_first_rank": component_rank,
                "elapsed_seconds": round(query_elapsed, 4),
                "retrieved": retrieved,
            }
        )

        print(
            query["id"],
            f"| page_rank={page_rank}",
            f"| component_rank={component_rank}",
            flush=True,
        )

    summary = {}

    for cutoff in CUTOFFS:
        for metric, rank_field in (
            ("page_hit", "page_first_rank"),
            ("component_hit", "component_first_rank"),
        ):
            hits = sum(
                item[rank_field] is not None and item[rank_field] <= cutoff for item in results
            )

            summary[f"{metric}_at_{cutoff}"] = {
                "hits": hits,
                "total": len(results),
                "rate": hits / len(results),
            }

    run_id = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S") + "_document_aware_retrieval"

    run_dir = RUNS_ROOT / run_id
    run_dir.mkdir(parents=True, exist_ok=False)

    report = {
        "run_id": run_id,
        "experiment": "document_aware_semantic_retrieval",
        "source_index": str(QDRANT_PATH.relative_to(ROOT)),
        "document_mapping": str(DOCUMENTS_PATH.relative_to(ROOT)),
        "retrieval_limit": TOP_K,
        "document_filter": None,
        "reranking": False,
        "page_grouping": False,
        "hit_definition": (
            "Page Hit requires matching document UUID and page; "
            "Component Hit additionally requires matching component type."
        ),
        "elapsed_seconds": round(perf_counter() - start, 3),
        "summary": summary,
        "results": results,
    }

    output = run_dir / "retrieval_report.json"

    output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print()
    print("SUMMARY")
    print(json.dumps(summary, indent=2))
    print()
    print("Saved:", output)


if __name__ == "__main__":
    main()
