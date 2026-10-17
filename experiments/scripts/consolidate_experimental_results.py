import json
import math
from pathlib import Path
from statistics import mean

RUN_ROOT = Path("experiments/runs")
OUTPUT_ROOT = Path("experiments/analysis")

RUNS = {
    "E1": {
        "retrieval": "20261009_015248_e1_retrieval/retrieval_report.json",
        "generation": "e1_budget5000_generation/generation_report.json",
        "faithfulness": "20261011_063034_e1_faithfulness/faithfulness_report.json",
        "relevancy": "20261011_072521_e1_response_relevancy/response_relevancy_report.json",
    },
    "E2": {
        "retrieval": "20261009_020206_e2_retrieval/retrieval_report.json",
        "generation": "e2_budget5000_generation/generation_report.json",
        "faithfulness": "20261011_070005_e2_faithfulness/faithfulness_report.json",
        "relevancy": "20261011_072911_e2_response_relevancy/response_relevancy_report.json",
    },
    "E3": {
        "retrieval": "20261008_053033_e3_document_aware_retrieval/retrieval_report.json",
        "generation": "20261008_055754_e3_generation/generation_report.json",
        "faithfulness": "20261008_062701_e3_faithfulness/faithfulness_report.json",
        "relevancy": "20261008_070558_e3_response_relevancy/response_relevancy_report.json",
    },
    "E4": {
        "retrieval": "20261008_032812_document_aware_retrieval/retrieval_report.json",
        "generation": "20260922_001610_generation/generation_report.json",
        "faithfulness": "20261001_210850_faithfulness/faithfulness_report.json",
        "relevancy": "20260930_232735_ragas/ragas_report.json",
    },
}


def load(relative_path):
    return json.loads((RUN_ROOT / relative_path).read_text(encoding="utf-8"))


def index_results(report, description):
    rows = report["results"]
    indexed = {row["id"]: row for row in rows}

    if len(rows) != 26 or len(indexed) != 26:
        raise ValueError(f"{description}: esperado 26 IDs únicos")

    return indexed


def valid(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def hit(rank, limit):
    return isinstance(rank, int) and 1 <= rank <= limit


def metric_summary(values):
    valid_values = [value for value in values if valid(value)]
    return {
        "valid": len(valid_values),
        "total": len(values),
        "mean": mean(valid_values) if valid_values else None,
    }


def main():
    datasets = {}
    configurations = {}

    for name, paths in RUNS.items():
        retrieval = index_results(load(paths["retrieval"]), f"{name} retrieval")
        generation = index_results(load(paths["generation"]), f"{name} generation")
        faithfulness = index_results(load(paths["faithfulness"]), f"{name} faithfulness")
        relevancy = index_results(load(paths["relevancy"]), f"{name} relevancy")

        ids = set(retrieval)
        if not (ids == set(generation) == set(faithfulness) == set(relevancy)):
            raise ValueError(f"{name}: conjuntos de perguntas divergentes")

        successes = sum(row["status"] == "success" for row in generation.values())
        if successes != 26:
            raise ValueError(f"{name}: geração incompleta")

        generation_times = [
            row["elapsed_seconds"]
            for row in generation.values()
            if valid(row.get("elapsed_seconds"))
        ]

        faith_scores = {query_id: row["faithfulness"] for query_id, row in faithfulness.items()}
        relevancy_scores = {
            query_id: row["response_relevancy"] for query_id, row in relevancy.items()
        }

        if not all(valid(value) for value in relevancy_scores.values()):
            raise ValueError(f"{name}: Response Relevancy inválido")

        page_hits = {
            str(k): sum(hit(row["page_first_rank"], k) for row in retrieval.values())
            for k in (5, 10, 20)
        }

        has_components = all("component_first_rank" in row for row in retrieval.values())

        component_hits = (
            {
                str(k): sum(hit(row["component_first_rank"], k) for row in retrieval.values())
                for k in (5, 10, 20)
            }
            if has_components
            else None
        )

        breakdown = {}
        for evidence_type in ("figure", "table", "plain_text"):
            group_ids = [
                query_id
                for query_id, row in retrieval.items()
                if row["expected_component_type"] == evidence_type
            ]
            breakdown[evidence_type] = {
                "questions": len(group_ids),
                "page_hit_at_20": sum(
                    hit(retrieval[qid]["page_first_rank"], 20) for qid in group_ids
                ),
                "component_hit_at_20": (
                    sum(hit(retrieval[qid]["component_first_rank"], 20) for qid in group_ids)
                    if has_components
                    else None
                ),
                "mean_response_relevancy": mean(relevancy_scores[qid] for qid in group_ids),
            }

        datasets[name] = {
            "retrieval": retrieval,
            "faithfulness": faith_scores,
        }

        configurations[name] = {
            "sources": paths,
            "questions": 26,
            "generation_successes": successes,
            "generation_elapsed_seconds_sum": sum(generation_times),
            "generation_timing_records": len(generation_times),
            "page_hits": page_hits,
            "component_hits": component_hits,
            "faithfulness_all_valid": metric_summary(list(faith_scores.values())),
            "response_relevancy": metric_summary(list(relevancy_scores.values())),
            "by_evidence_type": breakdown,
        }

    reference_ids = set(datasets["E1"]["retrieval"])
    if any(set(data["retrieval"]) != reference_ids for data in datasets.values()):
        raise ValueError("Perguntas de retrieval divergentes")

    for query_id in reference_ids:
        types = {datasets[name]["retrieval"][query_id]["expected_component_type"] for name in RUNS}
        if len(types) != 1:
            raise ValueError(f"Tipo divergente: {query_id}")

    paired_ids = sorted(
        query_id
        for query_id in reference_ids
        if all(valid(datasets[name]["faithfulness"][query_id]) for name in RUNS)
    )

    if len(paired_ids) != 24:
        raise ValueError(f"Esperadas 24 perguntas pareadas, obtidas {len(paired_ids)}")

    for name in RUNS:
        configurations[name]["faithfulness_paired"] = {
            "questions": len(paired_ids),
            "mean": mean(datasets[name]["faithfulness"][query_id] for query_id in paired_ids),
        }

    result = {
        "protocol": {
            "questions": 26,
            "retrieval_top_k": 20,
            "faithfulness_paired_questions": paired_ids,
            "faithfulness_excluded_questions": sorted(reference_ids - set(paired_ids)),
            "notes": [
                "Faithfulness pareado usa as mesmas 24 perguntas.",
                "Response Relevancy usa as 26 perguntas.",
                "Component Hit usa documento, pagina e tipo, nao ID exato.",
                "Component Hit nao se aplica diretamente a E1/E2.",
                "E1/E2 usam orcamento de entrada de 5000 tokens.",
                "Tempos registrados nao equivalem necessariamente a custo isolado do modelo.",
            ],
        },
        "configurations": configurations,
    }

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    output = OUTPUT_ROOT / "experimental_results_master.json"
    output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print("=== CONSOLIDACAO EXPERIMENTAL ===")
    print("Perguntas: 26")
    print("Faithfulness pareado:", len(paired_ids))
    print("Excluidas:", ", ".join(result["protocol"]["faithfulness_excluded_questions"]))

    for name, item in configurations.items():
        faith = item["faithfulness_paired"]["mean"]
        relevance = item["response_relevancy"]["mean"]
        page = item["page_hits"]["20"]

        print(
            f"{name}: Page Hit@20={page}/26 | Faithfulness={faith:.4f} | Relevancy={relevance:.4f}"
        )

    print("Relatorio:", output)


if __name__ == "__main__":
    main()
