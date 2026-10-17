import json
from pathlib import Path

QUERIES_DIR = Path("data/evaluation_dataset/queries")

REPORT_FILE = Path("experiments/runs/20260919_203148_retrieval/retrieval_report.json")

LIMITS = (5, 10, 20)


def load_gold_queries() -> dict[str, dict]:
    gold = {}

    for path in sorted(QUERIES_DIR.glob("*_queries.json")):
        queries = json.loads(path.read_text(encoding="utf-8"))

        for query in queries:
            gold[query["id"]] = query

    return gold


def main() -> None:
    gold = load_gold_queries()

    report = json.loads(REPORT_FILE.read_text(encoding="utf-8"))

    results = report["results"]

    print(
        "Source run:",
        report["run_id"],
    )
    print(
        "Queries:",
        len(results),
    )

    for limit in LIMITS:
        page_hits = 0
        component_hits = 0

        for result in results:
            query = gold[result["id"]]
            expected = query["expected_evidence"]

            expected_page = expected["page"]
            expected_type = expected["component_type"]

            pages = result["retrieved_pages"][:limit]
            types = result["retrieved_component_types"][:limit]

            page_hit = expected_page in pages

            component_hit = any(
                page == expected_page and component_type == expected_type
                for page, component_type in zip(
                    pages,
                    types,
                    strict=True,
                )
            )

            page_hits += int(page_hit)
            component_hits += int(component_hit)

        total = len(results)

        print()
        print(f"Hit@{limit}")
        print(
            "  Page:",
            f"{page_hits}/{total}",
            f"({page_hits / total:.4f})",
        )
        print(
            "  Component:",
            f"{component_hits}/{total}",
            f"({component_hits / total:.4f})",
        )


if __name__ == "__main__":
    main()
