import json
import time
import warnings
from datetime import datetime
from importlib.metadata import version
from pathlib import Path

from ragas.dataset_schema import SingleTurnSample

with warnings.catch_warnings():
    warnings.simplefilter("ignore", DeprecationWarning)
    from ragas.metrics import Faithfulness, ResponseRelevancy

from edgar.evaluation.ragas_embeddings import RagasModalEmbeddings
from edgar.evaluation.ragas_llm import RagasModalLLM
from edgar.infrastructure.modal_answer_generation_client import (
    ModalAnswerGenerationClient,
)
from edgar.infrastructure.modal_answer_generator import ModalAnswerGenerator
from edgar.infrastructure.modal_embedding_client import ModalEmbeddingClient
from edgar.infrastructure.modal_text_embedder import ModalTextEmbedder

SOURCE_REPORT = Path("experiments/runs/20260922_001610_generation/generation_report.json")

RUNS_DIR = Path("experiments/runs")

EVALUATOR_MAX_NEW_TOKENS = 512
RESPONSE_RELEVANCY_STRICTNESS = 1


def save_report(
    *,
    path: Path,
    report: dict,
) -> None:
    path.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def mean(
    values: list[float],
) -> float | None:
    if not values:
        return None

    return sum(values) / len(values)


def main() -> None:
    source = json.loads(SOURCE_REPORT.read_text(encoding="utf-8"))

    source_results = source["results"]

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    run_dir = RUNS_DIR / (f"{timestamp}_ragas")
    run_dir.mkdir(
        parents=True,
        exist_ok=False,
    )

    report_path = run_dir / "ragas_report.json"

    ragas_llm = RagasModalLLM(
        generator=ModalAnswerGenerator(
            client=ModalAnswerGenerationClient(),
            max_new_tokens=(EVALUATOR_MAX_NEW_TOKENS),
        ),
    )

    ragas_embeddings = RagasModalEmbeddings(
        embedder=ModalTextEmbedder(
            client=ModalEmbeddingClient(),
        ),
    )

    faithfulness_metric = Faithfulness(
        llm=ragas_llm,
        max_retries=1,
    )

    relevancy_metric = ResponseRelevancy(
        llm=ragas_llm,
        embeddings=ragas_embeddings,
        strictness=(RESPONSE_RELEVANCY_STRICTNESS),
    )

    report = {
        "run_id": timestamp,
        "source_generation_report": str(SOURCE_REPORT),
        "configuration": {
            "ragas_version": version("ragas"),
            "metrics_api": ("ragas.metrics legacy API"),
            "metrics": [
                "faithfulness",
                "answer_relevancy",
            ],
            "evaluator_max_new_tokens": (EVALUATOR_MAX_NEW_TOKENS),
            "response_relevancy_strictness": (RESPONSE_RELEVANCY_STRICTNESS),
            "faithfulness_max_retries": 1,
        },
        "results": [],
        "summary": {},
    }

    save_report(
        path=report_path,
        report=report,
    )

    total_start = time.perf_counter()

    total = len(source_results)

    for index, result in enumerate(
        source_results,
        start=1,
    ):
        query_id = result["id"]

        print(f"[{index}/{total}] {query_id}")

        sample = SingleTurnSample(
            user_input=result["user_input"],
            response=result["response"],
            retrieved_contexts=(result["retrieved_contexts"]),
            reference=result["reference"],
        )

        evaluation = {
            "id": query_id,
            "document": result.get("document"),
            "question_type": result.get("question_type"),
            "difficulty": result.get("difficulty"),
            "evaluation_category": result.get("evaluation_category"),
            "user_input": result["user_input"],
            "response": result["response"],
            "reference": result["reference"],
            "faithfulness": None,
            "response_relevancy": None,
            "faithfulness_elapsed_seconds": None,
            "response_relevancy_elapsed_seconds": None,
            "faithfulness_error": None,
            "response_relevancy_error": None,
        }

        metric_start = time.perf_counter()

        try:
            evaluation["faithfulness"] = faithfulness_metric.single_turn_score(sample)
        except Exception as error:
            evaluation["faithfulness_error"] = f"{type(error).__name__}: {error}"

        evaluation["faithfulness_elapsed_seconds"] = time.perf_counter() - metric_start

        report["results"].append(evaluation)

        save_report(
            path=report_path,
            report=report,
        )

        metric_start = time.perf_counter()

        try:
            evaluation["response_relevancy"] = relevancy_metric.single_turn_score(sample)
        except Exception as error:
            evaluation["response_relevancy_error"] = f"{type(error).__name__}: {error}"

        evaluation["response_relevancy_elapsed_seconds"] = time.perf_counter() - metric_start

        faithfulness_values = [
            item["faithfulness"] for item in report["results"] if item["faithfulness"] is not None
        ]

        relevancy_values = [
            item["response_relevancy"]
            for item in report["results"]
            if item["response_relevancy"] is not None
        ]

        report["summary"] = {
            "completed_queries": len(report["results"]),
            "total_queries": total,
            "faithfulness_successes": len(faithfulness_values),
            "response_relevancy_successes": len(relevancy_values),
            "mean_faithfulness": mean(faithfulness_values),
            "mean_response_relevancy": mean(relevancy_values),
            "elapsed_seconds": (time.perf_counter() - total_start),
        }

        save_report(
            path=report_path,
            report=report,
        )

        print(
            "  Faithfulness:",
            evaluation["faithfulness"],
        )
        print(
            "  Response Relevancy:",
            evaluation["response_relevancy"],
        )

    print()
    print("Evaluation completed.")
    print("Report:", report_path)
    print(
        "Mean Faithfulness:",
        report["summary"]["mean_faithfulness"],
    )
    print(
        "Mean Response Relevancy:",
        report["summary"]["mean_response_relevancy"],
    )


if __name__ == "__main__":
    main()
