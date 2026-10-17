import argparse
import json
from datetime import datetime
from pathlib import Path
from time import perf_counter
from types import SimpleNamespace

from huggingface_hub import hf_hub_download
from tokenizers import Tokenizer

from edgar.generation.prompts import build_grounded_answer_prompt
from edgar.infrastructure.modal_answer_generation_client import (
    ModalAnswerGenerationClient,
)
from edgar.infrastructure.modal_answer_generator import ModalAnswerGenerator
from edgar.retrieval.context import build_evidence_context

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "experiments/runs"
QUERY_DIR = ROOT / "data/evaluation_dataset/queries"

CONFIGS = {
    "e1": {
        "retrieval": "20261009_015248_e1_retrieval",
        "dataset": "e1_records.jsonl",
    },
    "e2": {
        "retrieval": "20261009_020206_e2_retrieval",
        "dataset": "e2_records.jsonl",
    },
}

TOKEN_BUDGET = 5000
RETRIEVAL_LIMIT = 20
MAX_NEW_TOKENS = 128

SYSTEM_MESSAGE = (
    "Você é o módulo de geração fundamentada do sistema EDGAR. "
    "Use somente informações explicitamente presentes nas "
    "evidências fornecidas. Não acrescente conhecimento externo, "
    "definições ou expansões de siglas."
)


def load_inputs(baseline):
    config = CONFIGS[baseline]

    retrieval_path = RUNS / config["retrieval"] / "retrieval_report.json"
    dataset_path = ROOT / "experiments/datasets/text_baselines" / config["dataset"]

    retrieval = json.loads(retrieval_path.read_text(encoding="utf-8"))

    records = {
        row["component_id"]: row
        for row in (
            json.loads(line) for line in dataset_path.read_text(encoding="utf-8").splitlines()
        )
    }

    queries = {}

    for path in sorted(QUERY_DIR.glob("*_queries.json")):
        for query in json.loads(path.read_text(encoding="utf-8")):
            if query["id"] in queries:
                raise RuntimeError("Duplicate query ID.")
            queries[query["id"]] = query

    results = retrieval["results"]

    if len(results) != 26 or len(queries) != 26:
        raise RuntimeError("Expected 26 queries.")

    if {row["id"] for row in results} != set(queries):
        raise RuntimeError("Retrieval/query ID mismatch.")

    for row in results:
        if row["question"] != queries[row["id"]]["question"]:
            raise RuntimeError(f"Question mismatch: {row['id']}")

        if len(row["retrieved"]) != RETRIEVAL_LIMIT:
            raise RuntimeError(f"Unexpected retrieval size: {row['id']}")

        for hit in row["retrieved"]:
            if hit["component_id"] not in records:
                raise RuntimeError(f"Missing component: {hit['component_id']}")

    return retrieval_path, dataset_path, results, queries, records


def make_evidence(hit, record):
    return SimpleNamespace(
        bbox=SimpleNamespace(**record["bbox"]),
        page_number=record["page_number"],
        component_type=SimpleNamespace(value=record["component_type"]),
        score=hit["score"],
        text=record["text"],
        component_id=record["component_id"],
    )


def count_prompt_tokens(tokenizer, prompt):
    chat = (
        f"<|im_start|>system\n{SYSTEM_MESSAGE}<|im_end|>\n"
        f"<|im_start|>user\n{prompt}<|im_end|>\n"
        "<|im_start|>assistant\n"
    )

    return len(
        tokenizer.encode(
            chat,
            add_special_tokens=False,
        ).ids
    )


def select_evidences(tokenizer, question, ranked, records):
    selected = []
    selected_prompt = None
    selected_tokens = 0

    for hit in ranked:
        evidence = make_evidence(
            hit,
            records[hit["component_id"]],
        )

        candidate = selected + [evidence]

        prompt = build_grounded_answer_prompt(
            question=question,
            evidence_context=build_evidence_context(candidate),
        )

        tokens = count_prompt_tokens(tokenizer, prompt)

        if tokens > TOKEN_BUDGET:
            break

        selected = candidate
        selected_prompt = prompt
        selected_tokens = tokens

    if not selected:
        raise RuntimeError("No evidence fits within the token budget.")

    return selected, selected_prompt, selected_tokens


def save_report(path, report):
    temporary = path.with_suffix(".json.tmp")

    temporary.write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--baseline",
        choices=tuple(CONFIGS),
        required=True,
    )
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()

    retrieval_path, dataset_path, results, queries, records = load_inputs(args.baseline)

    tokenizer_path = hf_hub_download(
        repo_id="Qwen/Qwen2.5-7B-Instruct",
        filename="tokenizer.json",
        local_files_only=True,
    )
    tokenizer = Tokenizer.from_file(tokenizer_path)

    prepared = []

    for row in results:
        query = queries[row["id"]]

        evidences, prompt, tokens = select_evidences(
            tokenizer,
            query["question"],
            row["retrieved"],
            records,
        )

        prepared.append((query, row, evidences, prompt, tokens))

    counts = [len(evidences) for _, _, evidences, _, _ in prepared]

    print("=== BASELINE GENERATION ===")
    print("Baseline:", args.baseline.upper())
    print("Queries:", len(prepared))
    print("Retrieval limit:", RETRIEVAL_LIMIT)
    print("Token budget:", TOKEN_BUDGET)
    print("Max new tokens:", MAX_NEW_TOKENS)
    print("Minimum evidences:", min(counts))
    print("Maximum evidences:", max(counts))
    print(
        "Maximum estimated prompt tokens:",
        max(item[4] for item in prepared),
    )

    if not args.execute:
        print("\nDRY RUN: no generation performed.")
        return

    run_id = f"{args.baseline}_budget5000_generation"
    run_dir = RUNS / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    output = run_dir / "generation_report.json"

    expected_config = {
        "baseline": args.baseline.upper(),
        "retrieval_limit": RETRIEVAL_LIMIT,
        "token_budget": TOKEN_BUDGET,
        "max_new_tokens": MAX_NEW_TOKENS,
        "source_retrieval_report": str(retrieval_path.relative_to(ROOT)),
        "source_dataset": str(dataset_path.relative_to(ROOT)),
    }

    if output.exists():
        report = json.loads(output.read_text(encoding="utf-8"))

        if report["configuration"] != expected_config:
            raise RuntimeError("Existing report has a different configuration.")
    else:
        report = {
            "run_id": run_id,
            "experiment": "text_baseline_grounded_generation",
            "created_at": datetime.now().astimezone().isoformat(),
            "configuration": expected_config,
            "results": [],
        }
        save_report(output, report)

    completed = {row["id"]: row for row in report["results"]}

    if not set(completed).issubset({query["id"] for query, *_ in prepared}):
        raise RuntimeError("Unexpected IDs in existing report.")

    generator = ModalAnswerGenerator(
        client=ModalAnswerGenerationClient(),
        max_new_tokens=MAX_NEW_TOKENS,
    )

    for index, (
        query,
        retrieval,
        evidences,
        prompt,
        tokens,
    ) in enumerate(prepared, start=1):
        query_id = query["id"]

        if completed.get(query_id, {}).get("status") == "success":
            print(
                f"[{index}/26] {query_id}: already completed",
                flush=True,
            )
            continue

        print(
            f"[{index}/26] {query_id}: {len(evidences)} evidences, {tokens} tokens",
            flush=True,
        )

        started = perf_counter()

        evaluation = {
            "id": query_id,
            "document": query["document"],
            "question_type": query["question_type"],
            "difficulty": query["difficulty"],
            "evaluation_category": query["evaluation_category"],
            "user_input": query["question"],
            "reference": query["reference_answer"],
            "retrieved_evidence_count": len(retrieval["retrieved"]),
            "generation_evidence_count": len(evidences),
            "estimated_prompt_tokens": tokens,
            "evidences": [
                {
                    "rank": rank,
                    "component_id": evidence.component_id,
                    "page": evidence.page_number,
                    "component_type": evidence.component_type.value,
                    "score": evidence.score,
                    "text": evidence.text,
                }
                for rank, evidence in enumerate(
                    evidences,
                    start=1,
                )
            ],
            "retrieved_contexts": [evidence.text for evidence in evidences],
        }

        try:
            evaluation["response"] = generator.generate(
                prompt=prompt,
            )
            evaluation["status"] = "success"
        except Exception as error:
            evaluation["status"] = "error"
            evaluation["error"] = f"{type(error).__name__}: {error}"

        evaluation["elapsed_seconds"] = round(
            perf_counter() - started,
            3,
        )

        completed[query_id] = evaluation

        report["results"] = [
            completed[item["id"]] for item, *_ in prepared if item["id"] in completed
        ]

        report["summary"] = {
            "total_queries": len(prepared),
            "successful_queries": sum(row["status"] == "success" for row in report["results"]),
            "error_queries": sum(row["status"] == "error" for row in report["results"]),
        }

        save_report(output, report)

        print(
            f"  {evaluation['status']} ({evaluation['elapsed_seconds']}s)",
            flush=True,
        )

        if evaluation["status"] == "error":
            raise RuntimeError(f"Generation failed for {query_id}: {evaluation['error']}")

    print("\nGENERATION COMPLETED")
    print("Successful:", report["summary"]["successful_queries"])
    print("Report:", output)


if __name__ == "__main__":
    main()
