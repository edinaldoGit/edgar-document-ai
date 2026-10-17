import json
from pathlib import Path

DOCUMENTS_FILE = Path("data/evaluation_dataset/metadata/documents.json")

QUERIES_DIR = Path("data/evaluation_dataset/queries")

VALID_COMPONENT_TYPES = {
    "plain_text",
    "figure",
    "table",
    "isolate_formula",
}

VALID_CATEGORIES = {
    "text_retrieval",
    "visual_evidence",
    "table_retrieval",
    "multimodal_reasoning",
}


def load_documents() -> dict:
    documents = json.loads(DOCUMENTS_FILE.read_text(encoding="utf-8"))

    return {document["id"]: document for document in documents}


def validate_query_file(
    path: Path,
    documents: dict,
) -> list[str]:
    errors = []

    queries = json.loads(path.read_text(encoding="utf-8"))

    ids = set()

    for query in queries:
        query_id = query["id"]

        if query_id in ids:
            errors.append(f"{path.name}: ID duplicado {query_id}")

        ids.add(query_id)

        document_id = query["document"]

        if document_id not in documents:
            errors.append(f"{query_id}: documento inexistente {document_id}")
            continue

        document = documents[document_id]

        evidence = query["expected_evidence"]

        page = evidence["page"]
        source_page = evidence["source_page"]

        start = document["selected_pages"]["start"]
        end = document["selected_pages"]["end"]

        curated_page_count = end - start + 1

        if not 1 <= page <= curated_page_count:
            errors.append(
                f"{query_id}: página curada {page} fora do intervalo 1-{curated_page_count}"
            )

        if not start <= source_page <= end:
            errors.append(
                f"{query_id}: página original {source_page} fora do intervalo {start}-{end}"
            )

        expected_curated_page = source_page - start + 1

        if page != expected_curated_page:
            errors.append(
                f"{query_id}: mapeamento inconsistente: "
                f"source_page={source_page} deveria corresponder "
                f"a page={expected_curated_page}, não {page}"
            )

        component_type = query["expected_evidence"]["component_type"]

        if component_type not in VALID_COMPONENT_TYPES:
            errors.append(f"{query_id}: componente inválido {component_type}")

        category = query.get("evaluation_category")

        if category not in VALID_CATEGORIES:
            errors.append(f"{query_id}: categoria inválida {category}")

        reference_answer = query.get("reference_answer")

        if not isinstance(reference_answer, str) or not reference_answer.strip():
            errors.append(f"{query_id}: reference_answer ausente ou vazia")

    return errors


def main():
    documents = load_documents()

    errors = []

    for query_file in sorted(QUERIES_DIR.glob("*_queries.json")):
        print(
            "Validando:",
            query_file.name,
        )

        errors.extend(
            validate_query_file(
                query_file,
                documents,
            )
        )

    print()

    if errors:
        print("ERROS ENCONTRADOS:")

        for error in errors:
            print("-", error)

        raise SystemExit(1)

    print("Todas as consultas são válidas.")


if __name__ == "__main__":
    main()
