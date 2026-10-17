import argparse
import json
import math
import time
import warnings
from datetime import datetime
from importlib.metadata import version
from pathlib import Path

from ragas.dataset_schema import SingleTurnSample

with warnings.catch_warnings():
    warnings.simplefilter("ignore", DeprecationWarning)
    from ragas.metrics import ResponseRelevancy

from edgar.evaluation.ragas_embeddings import RagasModalEmbeddings
from edgar.evaluation.ragas_llm import RagasModalLLM
from edgar.infrastructure.modal_answer_generation_client import (
    ModalAnswerGenerationClient,
)
from edgar.infrastructure.modal_answer_generator import ModalAnswerGenerator
from edgar.infrastructure.modal_embedding_client import ModalEmbeddingClient
from edgar.infrastructure.modal_text_embedder import ModalTextEmbedder

SOURCE_REPORTS = {
    "e1": Path("experiments/runs/e1_budget5000_generation/generation_report.json"),
    "e2": Path("experiments/runs/e2_budget5000_generation/generation_report.json"),
}

RUNS_DIR = Path("experiments/runs")

EVALUATOR_MAX_NEW_TOKENS = 512
RESPONSE_RELEVANCY_STRICTNESS = 1


def save_report(path: Path, report: dict) -> None:
    path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", choices=("e1", "e2"), required=True)
    args = parser.parse_args()
    source_report = SOURCE_REPORTS[args.baseline]
    source = json.loads(source_report.read_text(encoding="utf-8"))
    results = source["results"]

    if len(results) != 26:
        raise RuntimeError(f"Expected 26 answers, found {len(results)}.")

    if any(item.get("status") != "success" for item in results):
        raise RuntimeError("Generation report contains unsuccessful answers.")

    ragas_llm = RagasModalLLM(
        generator=ModalAnswerGenerator(
            client=ModalAnswerGenerationClient(),
            max_new_tokens=EVALUATOR_MAX_NEW_TOKENS,
        ),
    )

    ragas_embeddings = RagasModalEmbeddings(
        embedder=ModalTextEmbedder(
            client=ModalEmbeddingClient(),
        ),
    )

    metric = ResponseRelevancy(
        llm=ragas_llm,
        embeddings=ragas_embeddings,
        strictness=RESPONSE_RELEVANCY_STRICTNESS,
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = RUNS_DIR / f"{timestamp}_{args.baseline}_response_relevancy"
    run_dir.mkdir(parents=True, exist_ok=False)

    output = run_dir / "response_relevancy_report.json"

    report = {
        "run_id": timestamp,
        "experiment": f"{args.baseline}_response_relevancy",
        "source_generation_report": str(source_report),
        "configuration": {
            "ragas_version": version("ragas"),
            "metrics_api": "ragas.metrics legacy API",
            "metric": "response_relevancy",
            "evaluator_max_new_tokens": EVALUATOR_MAX_NEW_TOKENS,
            "response_relevancy_strictness": RESPONSE_RELEVANCY_STRICTNESS,
        },
        "results": [],
        "summary": {},
    }

    start = time.perf_counter()
    save_report(output, report)

    for index, item in enumerate(results, start=1):
        print(f"[{index}/{len(results)}] {item['id']}", flush=True)

        sample = SingleTurnSample(
            user_input=item["user_input"],
            response=item["response"],
            retrieved_contexts=item["retrieved_contexts"],
            reference=item["reference"],
        )

        evaluation = {
            "id": item["id"],
            "response_relevancy": None,
            "elapsed_seconds": None,
            "error": None,
        }

        metric_start = time.perf_counter()

        try:
            score = float(metric.single_turn_score(sample))
            if not math.isfinite(score):
                raise ValueError("Non-finite evaluation score.")
            evaluation["response_relevancy"] = score
        except Exception as error:
            evaluation["error"] = f"{type(error).__name__}: {error}"

        evaluation["elapsed_seconds"] = round(
            time.perf_counter() - metric_start,
            3,
        )

        report["results"].append(evaluation)

        values = [
            row["response_relevancy"]
            for row in report["results"]
            if row["response_relevancy"] is not None
        ]

        report["summary"] = {
            "completed_queries": len(report["results"]),
            "total_queries": len(results),
            "successes": len(values),
            "errors": len(report["results"]) - len(values),
            "mean_response_relevancy": (sum(values) / len(values) if values else None),
            "elapsed_seconds": round(time.perf_counter() - start, 3),
        }

        save_report(output, report)

        print(
            "  Response Relevancy:",
            evaluation["response_relevancy"],
            flush=True,
        )
        if evaluation["error"]:
            print("  Error:", evaluation["error"], flush=True)

    print("\nEvaluation completed.")
    print("Report:", output)
    print(
        "Mean Response Relevancy:",
        report["summary"]["mean_response_relevancy"],
    )


if __name__ == "__main__":
    main()
