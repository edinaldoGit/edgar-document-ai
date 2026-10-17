import json
import time
import warnings
from datetime import datetime
from importlib.metadata import version
from pathlib import Path

from ragas.dataset_schema import SingleTurnSample

with warnings.catch_warnings():
    warnings.simplefilter("ignore", DeprecationWarning)
    from ragas.metrics import Faithfulness

from edgar.evaluation.ragas_llm import RagasModalLLM
from edgar.infrastructure.modal_answer_generation_client import (
    ModalAnswerGenerationClient,
)
from edgar.infrastructure.modal_answer_generator import ModalAnswerGenerator

SOURCE_REPORT = Path("experiments/runs/20260922_001610_generation/generation_report.json")

RUNS_DIR = Path("experiments/runs")

EVALUATOR_MAX_NEW_TOKENS = 512


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


def build_structured_contexts(
    evidences: list[dict],
) -> list[str]:
    return [
        (
            f"Evidence {evidence['rank']} | "
            f"page={evidence['page']} | "
            f"type={evidence['component_type']} | "
            f"score={evidence['score']:.4f}\n"
            f"{evidence['text']}"
        )
        for evidence in evidences
    ]


def main() -> None:
    source = json.loads(SOURCE_REPORT.read_text(encoding="utf-8"))

    source_results = source["results"]

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    run_dir = RUNS_DIR / (f"{timestamp}_faithfulness")
    run_dir.mkdir(
        parents=True,
        exist_ok=False,
    )

    report_path = run_dir / "faithfulness_report.json"

    ragas_llm = RagasModalLLM(
        generator=ModalAnswerGenerator(
            client=ModalAnswerGenerationClient(),
            max_new_tokens=(EVALUATOR_MAX_NEW_TOKENS),
        ),
    )

    metric = Faithfulness(
        llm=ragas_llm,
        max_retries=1,
    )

    report = {
        "run_id": timestamp,
        "source_generation_report": str(SOURCE_REPORT),
        "configuration": {
            "ragas_version": version("ragas"),
            "metrics_api": ("ragas.metrics legacy API"),
            "metric": "faithfulness",
            "evaluator_max_new_tokens": (EVALUATOR_MAX_NEW_TOKENS),
            "faithfulness_max_retries": 1,
            "context_representation": (
                "structured evidence with rank, page, component type, score, and text"
            ),
            "response_preprocessing": "none",
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

        structured_contexts = build_structured_contexts(result["evidences"])

        sample = SingleTurnSample(
            user_input=result["user_input"],
            response=result["response"],
            retrieved_contexts=(structured_contexts),
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
            "elapsed_seconds": None,
            "error": None,
        }

        metric_start = time.perf_counter()

        try:
            evaluation["faithfulness"] = metric.single_turn_score(sample)
        except Exception as error:
            evaluation["error"] = f"{type(error).__name__}: {error}"

        evaluation["elapsed_seconds"] = time.perf_counter() - metric_start

        report["results"].append(evaluation)

        values = [
            item["faithfulness"] for item in report["results"] if item["faithfulness"] is not None
        ]

        report["summary"] = {
            "completed_queries": len(report["results"]),
            "total_queries": total,
            "successes": len(values),
            "errors": sum(item["error"] is not None for item in report["results"]),
            "mean_faithfulness": mean(values),
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

        if evaluation["error"]:
            print(
                "  Error:",
                evaluation["error"],
            )

    print()
    print("Evaluation completed.")
    print("Report:", report_path)
    print(
        "Mean Faithfulness:",
        report["summary"]["mean_faithfulness"],
    )


if __name__ == "__main__":
    main()
