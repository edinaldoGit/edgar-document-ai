import argparse
import json
from datetime import datetime
from pathlib import Path
from time import perf_counter

from edgar.application.bootstrap import build_retriever

ROOT = Path(__file__).resolve().parents[2]
QUERY_DIR = ROOT / "data/evaluation_dataset/queries"
DOCUMENTS_PATH = ROOT / "experiments/datasets/documents.json"
RUNS_ROOT = ROOT / "experiments/runs"

BASELINES = {
    "e1": "e1_text_chunks",
    "e2": "e2_page_text",
}

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

    if len({item["id"] for item in queries}) != 26:
        raise RuntimeError("Duplicate query IDs.")

    if any(item["document"] not in document_ids for item in queries):
        raise RuntimeError("Unknown document in queries.")

    return document_ids, queries


def first_page_hit_rank(
    evidences,
    *,
    expected_doc_id,
    expected_page,
):
    for rank, evidence in enumerate(evidences, start=1):
        if str(evidence.doc_id) == expected_doc_id and evidence.page_number == expected_page:
            return rank

    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--baseline",
        choices=tuple(BASELINES),
        required=True,
    )
    args = parser.parse_args()

    baseline = args.baseline

    qdrant_path = ROOT / "storage/experiments" / BASELINES[baseline] / "qdrant"

    if not qdrant_path.is_dir():
        raise RuntimeError(f"Index not found: {qdrant_path}")

    document_ids, queries = load_dataset()

    retriever = build_retriever(
        qdrant_path=qdrant_path,
    )

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

        elapsed = perf_counter() - query_start

        if any(evidence.component_type.value != "plain_text" for evidence in evidences):
            raise RuntimeError(f"Unexpected evidence type: {query['id']}")

        page_rank = first_page_hit_rank(
            evidences,
            expected_doc_id=expected_doc_id,
            expected_page=gold["page"],
        )

        retrieved = [
            {
                "rank": rank,
                "component_id": str(evidence.component_id),
                "doc_id": str(evidence.doc_id),
                "page_number": evidence.page_number,
                "component_type": evidence.component_type.value,
                "score": evidence.score,
            }
            for rank, evidence in enumerate(
                evidences,
                start=1,
            )
        ]

        results.append(
            {
                "id": query["id"],
                "document": query["document"],
                "question": query["question"],
                "expected_doc_id": expected_doc_id,
                "expected_page": gold["page"],
                "expected_component_type": gold["component_type"],
                "page_first_rank": page_rank,
                "elapsed_seconds": round(elapsed, 4),
                "retrieved": retrieved,
            }
        )

        print(
            query["id"],
            f"| page_rank={page_rank}",
            flush=True,
        )

    summary = {}

    for cutoff in CUTOFFS:
        hits = sum(
            item["page_first_rank"] is not None and item["page_first_rank"] <= cutoff
            for item in results
        )

        summary[f"page_hit_at_{cutoff}"] = {
            "hits": hits,
            "total": len(results),
            "rate": hits / len(results),
        }

    run_id = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S") + f"_{baseline}_retrieval"

    run_dir = RUNS_ROOT / run_id
    run_dir.mkdir(parents=True, exist_ok=False)

    report = {
        "run_id": run_id,
        "experiment": f"{baseline}_text_baseline_retrieval",
        "source_index": str(qdrant_path.relative_to(ROOT)),
        "document_mapping": str(DOCUMENTS_PATH.relative_to(ROOT)),
        "retrieval_limit": TOP_K,
        "document_filter": None,
        "reranking": False,
        "page_grouping": False,
        "metric": "page_hit",
        "hit_definition": ("Matching document UUID and page number."),
        "elapsed_seconds": round(
            perf_counter() - start,
            3,
        ),
        "summary": summary,
        "results": results,
    }

    output = run_dir / "retrieval_report.json"

    output.write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print("\nSUMMARY")
    print(json.dumps(summary, indent=2))
    print("\nSaved:", output)


if __name__ == "__main__":
    main()
