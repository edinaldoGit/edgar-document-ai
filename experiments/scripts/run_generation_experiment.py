import json
from datetime import datetime
from pathlib import Path
from time import perf_counter

from edgar.application.bootstrap import build_answering_pipeline

QUERIES_DIR = Path("data/evaluation_dataset/queries")

QDRANT_PATH = Path("storage/experiments/20260919_182500_corpus_ingestion/qdrant")

RUNS_DIR = Path("experiments/runs")

RETRIEVAL_LIMIT = 20
MAX_NEW_TOKENS = 128


def load_queries() -> list[dict]:
    queries = []

    for path in sorted(QUERIES_DIR.glob("*_queries.json")):
        queries.extend(json.loads(path.read_text(encoding="utf-8")))

    return queries


def save_report(
    path: Path,
    report: dict,
) -> None:
    path.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    queries = load_queries()

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S") + "_generation"

    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(
        parents=True,
        exist_ok=False,
    )

    report_path = run_dir / "generation_report.json"

    pipeline = build_answering_pipeline(
        qdrant_path=QDRANT_PATH,
        max_new_tokens=MAX_NEW_TOKENS,
    )

    report = {
        "run_id": run_id,
        "experiment": "grounded_answer_generation",
        "queries": len(queries),
        "retrieval_limit": RETRIEVAL_LIMIT,
        "max_new_tokens": MAX_NEW_TOKENS,
        "results": [],
    }

    total_start = perf_counter()

    for index, query in enumerate(
        queries,
        start=1,
    ):
        print(f"[{index}/{len(queries)}] {query['id']}")

        start = perf_counter()

        try:
            result = pipeline.answer(
                query["question"],
                limit=RETRIEVAL_LIMIT,
            )

            elapsed = perf_counter() - start

            evidences = [
                {
                    "rank": rank,
                    "page": evidence.page_number,
                    "component_type": (evidence.component_type.value),
                    "score": evidence.score,
                    "text": evidence.text,
                }
                for rank, evidence in enumerate(
                    result.evidences,
                    start=1,
                )
            ]

            report["results"].append(
                {
                    "id": query["id"],
                    "document": query["document"],
                    "question_type": query["question_type"],
                    "difficulty": query["difficulty"],
                    "evaluation_category": query["evaluation_category"],
                    "user_input": query["question"],
                    "response": result.answer,
                    "reference": query["reference_answer"],
                    "retrieved_contexts": [evidence["text"] for evidence in evidences],
                    "evidences": evidences,
                    "elapsed_seconds": round(
                        elapsed,
                        3,
                    ),
                    "status": "success",
                }
            )

            print(f"  concluída em {elapsed:.2f}s")

        except Exception as exc:
            elapsed = perf_counter() - start

            report["results"].append(
                {
                    "id": query["id"],
                    "document": query["document"],
                    "question_type": query["question_type"],
                    "difficulty": query["difficulty"],
                    "evaluation_category": query["evaluation_category"],
                    "user_input": query["question"],
                    "reference": query["reference_answer"],
                    "status": "error",
                    "error": (f"{type(exc).__name__}: {exc}"),
                    "elapsed_seconds": round(
                        elapsed,
                        3,
                    ),
                }
            )

            print(f"  ERRO após {elapsed:.2f}s: {type(exc).__name__}: {exc}")

        report["elapsed_seconds"] = round(
            perf_counter() - total_start,
            3,
        )

        save_report(
            report_path,
            report,
        )

    print()
    print(
        "Generation experiment completed:",
        run_id,
    )
    print(
        "Queries:",
        len(report["results"]),
    )
    print(
        "Elapsed:",
        report["elapsed_seconds"],
        "seconds",
    )
    print(
        "Report:",
        report_path,
    )


if __name__ == "__main__":
    main()
