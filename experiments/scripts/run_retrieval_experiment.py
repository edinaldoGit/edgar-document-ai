import json
from datetime import datetime
from pathlib import Path
from time import perf_counter

from edgar.application.bootstrap import build_retriever
from edgar.retrieval.page_grouping import PageEvidenceGrouper
from edgar.retrieval.reranking import EvidenceReranker

PROJECT_ROOT = Path(__file__).resolve().parents[2]

QUERY_DIR = PROJECT_ROOT / "data" / "evaluation_dataset" / "queries"

QDRANT_PATH = (
    PROJECT_ROOT / "storage" / "experiments" / "20260919_182500_corpus_ingestion" / "qdrant"
)

RUNS_ROOT = PROJECT_ROOT / "experiments" / "runs"


def load_queries():
    queries = []

    for path in sorted(QUERY_DIR.glob("*_queries.json")):
        queries.extend(json.loads(path.read_text(encoding="utf-8")))

    return queries


def main():
    run_id = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S") + "_retrieval"

    run_dir = RUNS_ROOT / run_id
    run_dir.mkdir(parents=True, exist_ok=False)

    retriever = build_retriever(
        qdrant_path=QDRANT_PATH,
    )

    reranker = EvidenceReranker()
    page_grouper = PageEvidenceGrouper()

    queries = load_queries()

    results = []

    start = perf_counter()

    for query in queries:
        retrieved = retriever.retrieve(
            query["question"],
            limit=20,
        )

        grouped_pages = page_grouper.group(
            retrieved,
            limit=5,
        )

        retrieved = [component for page in grouped_pages for component in page.components]

        retrieved = reranker.rerank(
            retrieved,
            question_type=query["question_type"],
            limit=5,
        )

        expected = query["expected_evidence"]

        retrieved_pages = [evidence.page_number for evidence in retrieved]

        retrieved_types = [evidence.component_type.value for evidence in retrieved]

        page_hit = expected["page"] in retrieved_pages

        component_hit = any(
            evidence.page_number == expected["page"]
            and evidence.component_type.value == expected["component_type"]
            for evidence in retrieved
        )

        results.append(
            {
                "id": query["id"],
                "document": query["document"],
                "question": query["question"],
                "expected_page": expected["page"],
                "expected_component_type": expected["component_type"],
                "retrieved_pages": retrieved_pages,
                "retrieved_component_types": retrieved_types,
                "page_hit": page_hit,
                "component_hit": component_hit,
            }
        )

    elapsed = perf_counter() - start

    report = {
        "run_id": run_id,
        "experiment": "retrieval_evaluation",
        "queries": len(results),
        "elapsed_seconds": round(elapsed, 3),
        "page_hit_rate": round(
            sum(r["page_hit"] for r in results) / len(results),
            4,
        ),
        "component_hit_rate": round(
            sum(r["component_hit"] for r in results) / len(results),
            4,
        ),
        "results": results,
    }

    (run_dir / "retrieval_report.json").write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"Retrieval experiment completed: {run_id}")
    print(f"Queries: {len(results)}")
    print(f"Page hit rate: {report['page_hit_rate']}")
    print(f"Component hit rate: {report['component_hit_rate']}")


if __name__ == "__main__":
    main()
