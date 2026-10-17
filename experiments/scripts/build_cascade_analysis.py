import json
from collections import defaultdict
from pathlib import Path
from statistics import mean

QUERY_FILES = [
    Path("data/evaluation_dataset/queries/calculus_queries.json"),
    Path("data/evaluation_dataset/queries/graphs_queries.json"),
    Path("data/evaluation_dataset/queries/physics_queries.json"),
    Path("data/evaluation_dataset/queries/statistics_queries.json"),
]

RETRIEVAL_REPORT = Path("experiments/runs/20260919_203148_retrieval/retrieval_report.json")

GENERATION_SUMMARY = Path("experiments/analysis/generation_metrics_summary.json")

OUTPUT = Path("experiments/analysis/cascade_error_analysis.json")


def first_rank(
    values: list,
    expected,
) -> int | None:
    for rank, value in enumerate(
        values,
        start=1,
    ):
        if value == expected:
            return rank

    return None


def first_pair_rank(
    pages: list[int],
    component_types: list[str],
    expected_page: int,
    expected_component_type: str,
) -> int | None:
    for rank, (
        page,
        component_type,
    ) in enumerate(
        zip(
            pages,
            component_types,
            strict=True,
        ),
        start=1,
    ):
        if page == expected_page and component_type == expected_component_type:
            return rank

    return None


def mean_or_none(
    values: list[float],
) -> float | None:
    if not values:
        return None

    return mean(values)


queries = {}

for path in QUERY_FILES:
    data = json.loads(path.read_text(encoding="utf-8"))

    for query in data:
        query_id = query["id"]

        if query_id in queries:
            raise RuntimeError(f"Duplicate query ID: {query_id}")

        queries[query_id] = query


retrieval_report = json.loads(RETRIEVAL_REPORT.read_text(encoding="utf-8"))

generation_summary = json.loads(GENERATION_SUMMARY.read_text(encoding="utf-8"))

retrieval_by_id = {item["id"]: item for item in retrieval_report["results"]}

generation_by_id = {item["id"]: item for item in generation_summary["results"]}

expected_ids = set(queries)

if set(retrieval_by_id) != expected_ids:
    raise RuntimeError("Retrieval report IDs do not match the current query dataset.")

if set(generation_by_id) != expected_ids:
    raise RuntimeError("Generation summary IDs do not match the current query dataset.")


results = []

for query_id, query in sorted(queries.items()):
    gold = query["expected_evidence"]
    retrieval = retrieval_by_id[query_id]
    generation = generation_by_id[query_id]

    expected_page = gold["page"]
    expected_component_type = gold["component_type"]

    retrieved_pages = retrieval["retrieved_pages"]
    retrieved_component_types = retrieval["retrieved_component_types"]

    page_rank = first_rank(
        retrieved_pages,
        expected_page,
    )

    component_rank = first_pair_rank(
        retrieved_pages,
        retrieved_component_types,
        expected_page,
        expected_component_type,
    )

    page_hit_at_5 = page_rank is not None and page_rank <= 5
    page_hit_at_10 = page_rank is not None and page_rank <= 10
    page_hit_at_20 = page_rank is not None and page_rank <= 20

    component_hit_at_5 = component_rank is not None and component_rank <= 5
    component_hit_at_10 = component_rank is not None and component_rank <= 10
    component_hit_at_20 = component_rank is not None and component_rank <= 20

    if component_hit_at_20:
        retrieval_status = "exact_component_hit"
    elif page_hit_at_20:
        retrieval_status = "page_only_hit"
    else:
        retrieval_status = "page_miss"

    results.append(
        {
            "id": query_id,
            "document": query["document"],
            "question_type": query["question_type"],
            "difficulty": query["difficulty"],
            "evaluation_category": query["evaluation_category"],
            "expected_page": (expected_page),
            "expected_component_type": (expected_component_type),
            "page_first_rank": (page_rank),
            "component_first_rank": (component_rank),
            "page_hit_at_5": (page_hit_at_5),
            "page_hit_at_10": (page_hit_at_10),
            "page_hit_at_20": (page_hit_at_20),
            "component_hit_at_5": (component_hit_at_5),
            "component_hit_at_10": (component_hit_at_10),
            "component_hit_at_20": (component_hit_at_20),
            "retrieval_status_at_20": (retrieval_status),
            "faithfulness": generation["faithfulness"],
            "faithfulness_valid": (generation["faithfulness_valid"]),
            "response_relevancy": (generation["response_relevancy"]),
        }
    )


def hit_count(
    field: str,
) -> int:
    return sum(item[field] for item in results)


status_groups = defaultdict(list)

for item in results:
    status_groups[item["retrieval_status_at_20"]].append(item)


by_retrieval_status = {}

for status, items in sorted(status_groups.items()):
    faithfulness_values = [item["faithfulness"] for item in items if item["faithfulness_valid"]]

    relevancy_values = [item["response_relevancy"] for item in items]

    by_retrieval_status[status] = {
        "queries": len(items),
        "faithfulness_valid_queries": len(faithfulness_values),
        "mean_faithfulness": (mean_or_none(faithfulness_values)),
        "mean_response_relevancy": (mean_or_none(relevancy_values)),
        "query_ids": [item["id"] for item in items],
    }


summary = {
    "total_queries": len(results),
    "page_hit_at_5": {
        "hits": hit_count("page_hit_at_5"),
        "rate": (hit_count("page_hit_at_5") / len(results)),
    },
    "page_hit_at_10": {
        "hits": hit_count("page_hit_at_10"),
        "rate": (hit_count("page_hit_at_10") / len(results)),
    },
    "page_hit_at_20": {
        "hits": hit_count("page_hit_at_20"),
        "rate": (hit_count("page_hit_at_20") / len(results)),
    },
    "component_hit_at_5": {
        "hits": hit_count("component_hit_at_5"),
        "rate": (hit_count("component_hit_at_5") / len(results)),
    },
    "component_hit_at_10": {
        "hits": hit_count("component_hit_at_10"),
        "rate": (hit_count("component_hit_at_10") / len(results)),
    },
    "component_hit_at_20": {
        "hits": hit_count("component_hit_at_20"),
        "rate": (hit_count("component_hit_at_20") / len(results)),
    },
    "by_retrieval_status_at_20": (by_retrieval_status),
}


output = {
    "sources": {
        "query_files": [str(path) for path in QUERY_FILES],
        "retrieval_report": str(RETRIEVAL_REPORT),
        "generation_summary": str(GENERATION_SUMMARY),
    },
    "method": {
        "page_gold_field": ("expected_evidence.page"),
        "component_hit_definition": (
            "expected page and expected component type occur in the same retrieved result"
        ),
        "retrieval_scope": ("corpus-wide top-20"),
    },
    "summary": summary,
    "results": results,
}

OUTPUT.write_text(
    json.dumps(
        output,
        indent=2,
        ensure_ascii=False,
    ),
    encoding="utf-8",
)


print("RETRIEVAL RECALCULADO")
print(
    "Page Hit@5:",
    summary["page_hit_at_5"],
)
print(
    "Page Hit@10:",
    summary["page_hit_at_10"],
)
print(
    "Page Hit@20:",
    summary["page_hit_at_20"],
)
print(
    "Component Hit@5:",
    summary["component_hit_at_5"],
)
print(
    "Component Hit@10:",
    summary["component_hit_at_10"],
)
print(
    "Component Hit@20:",
    summary["component_hit_at_20"],
)

print()
print("POR STATUS DE RETRIEVAL @20")

for status, values in by_retrieval_status.items():
    faithfulness = values["mean_faithfulness"]
    relevancy = values["mean_response_relevancy"]

    print(
        status,
        "| n=",
        values["queries"],
        "| faith_n=",
        values["faithfulness_valid_queries"],
        "| Faithfulness=",
        (f"{faithfulness:.4f}" if faithfulness is not None else "N/A"),
        "| ResponseRelevancy=",
        (f"{relevancy:.4f}" if relevancy is not None else "N/A"),
    )

print()
print("Salvo em:", OUTPUT)
